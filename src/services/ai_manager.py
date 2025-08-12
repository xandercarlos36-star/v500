import os
import logging
import time
import json
from typing import Dict, List, Optional, Any
import requests

# Imports condicionais para os clientes de IA
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from services.groq_client import groq_client
    HAS_GROQ_CLIENT = True
except ImportError:
    HAS_GROQ_CLIENT = False

logger = logging.getLogger(__name__)

class AIManager:
    """Gerenciador de IAs com sistema de fallback automático"""

    def __init__(self):
        """Inicializa o gerenciador de IAs"""
        self.providers = {
            'gemini': {
                'client': None,
                'available': False,
                'priority': 1,  # GEMINI PRO CONFIRMADO COMO PRIORIDADE MÁXIMA
                'error_count': 0,
                'model': 'gemini-2.5-pro',  # Gemini 2.5 Pro
                'max_errors': 2,
                'last_success': None,
                'consecutive_failures': 0,
                'enabled': True # Adicionado campo enabled
            },
            'groq': {
                'client': None,
                'available': False,
                'priority': 2,  # FALLBACK AUTOMÁTICO
                'error_count': 0,
                'model': 'llama3-70b-8192',
                'max_errors': 2,
                'last_success': None,
                'consecutive_failures': 0,
                'enabled': True # Adicionado campo enabled
            },
            'openai': {
                'client': None,
                'available': False,
                'priority': 3,
                'error_count': 0,
                'model': 'gpt-3.5-turbo',
                'max_errors': 2,
                'last_success': None,
                'consecutive_failures': 0,
                'enabled': True # Adicionado campo enabled
            },
            'huggingface': {
                'client': None,
                'available': False,
                'priority': 4,
                'error_count': 0,
                'models': ["HuggingFaceH4/zephyr-7b-beta", "google/flan-t5-base"],
                'current_model_index': 0,
                'max_errors': 3,
                'last_success': None,
                'consecutive_failures': 0,
                'enabled': True # Adicionado campo enabled
            }
        }

        self.initialize_providers()
        available_count = len([p for p in self.providers.values() if p['available']])
        logger.info(f"🤖 AI Manager inicializado com {available_count} provedores disponíveis.")

    def initialize_providers(self):
        """Inicializa todos os provedores de IA com base nas chaves de API disponíveis."""

        # Inicializa Gemini
        if HAS_GEMINI:
            try:
                gemini_key = os.getenv('GEMINI_API_KEY')
                if gemini_key:
                    genai.configure(api_key=gemini_key)
                    self.providers['gemini']['client'] = genai.GenerativeModel("gemini-2.5-pro")
                    self.providers['gemini']['available'] = True
                    logger.info("✅ Gemini 2.5 Pro (gemini-2.5-pro) inicializado como MODELO PRIMÁRIO")
            except Exception as e:
                logger.warning(f"⚠️ Falha ao inicializar Gemini: {str(e)}")
        else:
            logger.warning("⚠️ Biblioteca 'google-generativeai' não instalada.")

        # Inicializa OpenAI
        if HAS_OPENAI:
            try:
                openai_key = os.getenv('OPENAI_API_KEY')
                if openai_key:
                    self.providers["openai"]["client"] = openai.OpenAI(api_key=openai_key)
                    self.providers["openai"]["available"] = True
                    logger.info("✅ OpenAI (gpt-3.5-turbo) inicializado com sucesso")
            except Exception as e:
                logger.info(f"ℹ️ OpenAI não disponível: {str(e)}")
        else:
            logger.info("ℹ️ Biblioteca 'openai' não instalada.")

        # Inicializa Groq
        try:
            if HAS_GROQ_CLIENT and groq_client and groq_client.is_enabled():
                self.providers['groq']['client'] = groq_client
                self.providers['groq']['available'] = True
                logger.info("✅ Groq (llama3-70b-8192) inicializado com sucesso")
            else:
                logger.info("ℹ️ Groq client não configurado")
        except Exception as e:
            logger.info(f"ℹ️ Groq não disponível: {str(e)}")

        # Inicializa HuggingFace
        try:
            hf_key = os.getenv('HUGGINGFACE_API_KEY')
            if hf_key:
                self.providers['huggingface']['client'] = {
                    'api_key': hf_key,
                    'base_url': 'https://api-inference.huggingface.co/models/'
                }
                self.providers['huggingface']['available'] = True
                logger.info("✅ HuggingFace inicializado com sucesso")
        except Exception as e:
            logger.info(f"ℹ️ HuggingFace não disponível: {str(e)}")

    def get_best_provider(self) -> Optional[str]:
        """Retorna o melhor provedor disponível com base na prioridade e contagem de erros."""
        current_time = time.time()

        # Primeiro, tenta reabilitar provedores que podem ter se recuperado
        for name, provider in self.providers.items():
            if (not provider['available'] and 
                provider.get('last_success') and 
                current_time - provider['last_success'] > 300):  # 5 minutos
                logger.info(f"🔄 Tentando reabilitar provedor {name} após cooldown")
                provider['error_count'] = 0
                provider['consecutive_failures'] = 0
                if name == 'gemini' and HAS_GEMINI:
                    provider['available'] = True
                elif name == 'groq' and HAS_GROQ_CLIENT:
                    provider['available'] = True
                elif name == 'openai' and HAS_OPENAI:
                    provider['available'] = True
                elif name == 'huggingface':
                    provider['available'] = True

        available_providers = [
            (name, provider) for name, provider in self.providers.items() 
            if provider['available'] and provider['consecutive_failures'] < provider.get('max_errors', 2)
        ]

        if not available_providers:
            logger.warning("🔄 Nenhum provedor saudável disponível. Resetando contadores.")
            for provider in self.providers.values():
                provider['error_count'] = 0
                provider['consecutive_failures'] = 0
            available_providers = [(name, p) for name, p in self.providers.items() if p['available']]

        if available_providers:
            # Ordena por prioridade e falhas consecutivas
            available_providers.sort(key=lambda x: (x[1]['priority'], x[1]['consecutive_failures']))
            return available_providers[0][0]

        return None

    def generate_analysis(self, prompt: str, max_tokens: int = 4000, **kwargs) -> Dict[str, Any]:
        """Método para compatibilidade - redireciona para generate_response"""
        # CORREÇÃO CRÍTICA: Verifica se kwargs é None e substitui por dict vazio
        if kwargs is None:
            kwargs = {}

        return self.generate_response(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=kwargs.get('temperature', 0.7),
            system_prompt=kwargs.get('system_prompt'),
            **{k: v for k, v in kwargs.items() if k not in ['temperature', 'system_prompt']}
        )

    def generate_response(
            self,
            prompt: str,
            max_tokens: int = 4000,
            temperature: float = 0.7,
            system_prompt: str = None,
            **kwargs
        ) -> Dict[str, Any]:
            """Gera resposta usando o modelo primário com fallback automático"""
            try:
                # Usa o Gemini como modelo primário
                if self.providers.get('gemini', {}).get('available'):
                    try:
                        client = self.providers['gemini']['client']
                        response = client.generate_content(
                            prompt, 
                            generation_config={"temperature": temperature, "max_output_tokens": min(max_tokens, 8192)},
                            safety_settings=[
                                {"category": c, "threshold": "BLOCK_NONE"} 
                                for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]
                            ]
                        )
                        
                        # Extrai texto de forma robusta
                        content = self._extract_text_from_gemini_response(response)
                        if content and content != "Erro na extração":
                            self._record_success('gemini')
                            return {
                                'success': True,
                                'content': content,
                                'provider': 'gemini',
                                'error': None
                            }
                        else:
                            raise Exception("Resposta vazia ou inválida do Gemini")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Gemini falhou: {e}")
                        self._record_failure('gemini', str(e))

                # Fallback para outros modelos
                fallback_order = ['groq', 'openai', 'huggingface']

                for provider_name in fallback_order:
                    provider_info = self.providers.get(provider_name)
                    if provider_info and provider_info.get('available') and provider_info.get('client'):
                        try:
                            content = self._call_provider(provider_name, prompt, max_tokens)
                            if content:
                                self._record_success(provider_name)
                                return {
                                    'success': True,
                                    'content': content,
                                    'provider': provider_name,
                                    'error': None
                                }
                        except Exception as e:
                            logger.warning(f"⚠️ {provider_name} falhou: {e}")
                            self._record_failure(provider_name, str(e))
                            continue

                raise Exception("Todos os provedores de IA falharam")

            except Exception as e:
                logger.error(f"❌ Erro crítico no AI Manager: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'content': 'Erro na geração de resposta'
                }

    def _call_provider(self, provider_name: str, prompt: str, max_tokens: int) -> Optional[str]:
        """Chama a função de geração do provedor especificado."""
        if provider_name == 'gemini':
            return self._generate_with_gemini(prompt, max_tokens)
        elif provider_name == 'groq':
            return self._generate_with_groq(prompt, max_tokens)
        elif provider_name == 'openai':
            return self._generate_with_openai(prompt, max_tokens)
        elif provider_name == 'huggingface':
            return self._generate_with_huggingface(prompt, max_tokens)
        return None

    def _generate_with_gemini(self, prompt: str, max_tokens: int) -> Optional[str]:
        """Gera conteúdo usando Gemini."""
        client = self.providers['gemini']['client']
        config = {
            "temperature": 0.8,  # Criatividade controlada
            "max_output_tokens": min(max_tokens, 8192),
            "top_p": 0.95,
            "top_k": 64
        }
        safety = [
            {"category": c, "threshold": "BLOCK_NONE"} 
            for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]
        ]
        try:
            response = client.generate_content(prompt, generation_config=config, safety_settings=safety)
            content = self._extract_text_from_gemini_response(response)

            if content and "Erro na extração" not in content:
                logger.info(f"✅ Gemini 2.5 Pro gerou {len(content)} caracteres")
                return content
            elif "Erro na extração" in content:
                 raise Exception(content)
            else:
                raise Exception("Resposta vazia do Gemini 2.5 Pro")
        except Exception as e:
            logger.error(f"❌ Falha ao gerar com Gemini: {e}")
            raise e # Propaga a exceção para ser tratada pelo _call_provider e fallback

    def _extract_text_from_gemini_response(self, response) -> str:
        """Extrai texto da resposta do Gemini tratando diferentes formatos"""
        try:
            # Primeiro verifica se é uma resposta simples
            if hasattr(response, 'text') and response.text:
                try:
                    # Tenta acessar o texto diretamente
                    text_content = response.text
                    if text_content and isinstance(text_content, str):
                        return text_content.strip()
                except Exception:
                    # Se falhar, continua para o método de parts
                    pass

            # Método robusto para respostas com múltiplas partes
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            text_parts = []
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(str(part.text).strip())
                            if text_parts:
                                combined_text = ' '.join(text_parts)
                                if combined_text.strip():
                                    return combined_text.strip()

            # Tenta acessar via parts diretamente no response
            if hasattr(response, 'parts') and response.parts:
                text_parts = []
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(str(part.text).strip())
                if text_parts:
                    return ' '.join(text_parts).strip()

            # Fallback para responses que têm _result
            if hasattr(response, '_result') and response._result:
                return self._extract_text_from_gemini_response(response._result)

            # Se tudo falhar, tenta converter diretamente
            response_str = str(response)
            if response_str and response_str != 'None' and len(response_str) > 10:
                return response_str

            logger.warning("Resposta Gemini não contém texto válido")
            return "Resposta gerada mas sem conteúdo textual acessível"

        except Exception as e:
            logger.error(f"❌ Erro crítico ao extrair texto da resposta Gemini: {e}")
            return f"Erro na extração: conteúdo gerado mas inacessível ({str(e)[:100]})"


    def _generate_with_groq(self, prompt: str, max_tokens: int) -> Optional[str]:
        """Gera conteúdo usando Groq."""
        client = self.providers['groq']['client']
        content = client.generate(prompt, max_tokens=min(max_tokens, 8192))
        if content:
            logger.info(f"✅ Groq gerou {len(content)} caracteres")
            return content
        raise Exception("Resposta vazia do Groq")

    def _generate_with_openai(self, prompt: str, max_tokens: int) -> Optional[str]:
        """Gera conteúdo usando OpenAI."""
        client = self.providers['openai']['client']
        response = client.chat.completions.create(
            model=self.providers['openai']['model'],
            messages=[
                {"role": "system", "content": "Você é um especialista em análise de mercado ultra-detalhada."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=min(max_tokens, 4096),
            temperature=0.7
        )
        content = response.choices[0].message.content
        if content:
            logger.info(f"✅ OpenAI gerou {len(content)} caracteres")
            return content
        raise Exception("Resposta vazia do OpenAI")

    def _generate_with_huggingface(self, prompt: str, max_tokens: int) -> Optional[str]:
        """Gera conteúdo usando HuggingFace com rotação de modelos."""
        config = self.providers['huggingface']
        for _ in range(len(config['models'])):
            model_index = config['current_model_index']
            model = config['models'][model_index]
            config['current_model_index'] = (model_index + 1) % len(config['models']) # Rotaciona para a próxima vez

            try:
                url = f"{config['client']['base_url']}{model}"
                headers = {"Authorization": f"Bearer {config['client']['api_key']}"}
                payload = {"inputs": prompt, "parameters": {"max_new_tokens": min(max_tokens, 1024)}}
                response = requests.post(url, headers=headers, json=payload, timeout=60)

                if response.status_code == 200:
                    res_json = response.json()
                    content = res_json[0].get("generated_text", "")
                    if content:
                        logger.info(f"✅ HuggingFace ({model}) gerou {len(content)} caracteres")
                        return content
                elif response.status_code == 503:
                    logger.warning(f"⚠️ Modelo HuggingFace {model} está carregando (503), tentando próximo...")
                    continue
                else:
                    logger.warning(f"⚠️ Erro {response.status_code} no modelo {model}")
                    continue
            except Exception as e:
                logger.warning(f"⚠️ Erro no modelo {model}: {e}")
                continue
        raise Exception("Todos os modelos HuggingFace falharam")

    def reset_provider_errors(self, provider_name: str = None):
        """Reset contadores de erro dos provedores"""
        if provider_name:
            if provider_name in self.providers:
                self.providers[provider_name]['error_count'] = 0
                self.providers[provider_name]['consecutive_failures'] = 0
                self.providers[provider_name]['available'] = True
                logger.info(f"🔄 Reset erros do provedor: {provider_name}")
        else:
            for provider in self.providers.values():
                provider['error_count'] = 0
                provider['consecutive_failures'] = 0
                if provider.get('client'):  # Só reabilita se tem cliente configurado
                    provider['available'] = True
            logger.info("🔄 Reset erros de todos os provedores")

    def _try_fallback(self, prompt: str, max_tokens: int, exclude: List[str]) -> Optional[str]:
        """Tenta usar o próximo provedor disponível como fallback."""
        logger.info(f"🔄 Acionando fallback, excluindo: {', '.join(exclude)}")

        # Ordena provedores por prioridade, excluindo os que já falharam
        available_providers = [
            (name, provider) for name, provider in self.providers.items()
            if (provider['available'] and 
                name not in exclude and 
                provider['consecutive_failures'] < provider.get('max_errors', 2))
        ]

        if not available_providers:
            logger.critical("❌ Todos os provedores de fallback falharam.")
            return None

        # Ordena por prioridade
        available_providers.sort(key=lambda x: (x[1]['priority'], x[1]['consecutive_failures']))
        next_provider = available_providers[0][0]

        logger.info(f"🔄 Tentando fallback para: {next_provider.upper()}")

        try:
            result = self._call_provider(next_provider, prompt, max_tokens)
            if result:
                self._record_success(next_provider)
                return result
            else:
                raise Exception("Resposta vazia do fallback")
        except Exception as e:
            logger.error(f"❌ Fallback para {next_provider} também falhou: {e}")
            self._record_failure(next_provider, str(e))
            return self._try_fallback(prompt, max_tokens, exclude + [next_provider])

    def _record_failure(self, provider_name: str, error_message: str):
        """Registra falha de um provedor"""
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            provider['error_count'] += 1
            provider['consecutive_failures'] += 1
            
            # Desabilita provedor se exceder limite de erros
            if provider['consecutive_failures'] >= provider.get('max_errors', 2):
                provider['available'] = False
                logger.warning(f"⚠️ Provedor {provider_name} desabilitado após {provider['consecutive_failures']} falhas consecutivas")

    def _record_success(self, provider_name: str):
        """Registra sucesso de um provedor"""
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            provider['consecutive_failures'] = 0
            provider['last_success'] = time.time()
            if not provider['available']:
                provider['available'] = True
                logger.info(f"✅ Provedor {provider_name} reabilitado após sucesso")

    def get_provider_status(self) -> Dict[str, Any]:
        """Retorna status detalhado dos provedores"""
        status = {}

        for name, provider in self.providers.items():
            status[name] = {
                'available': provider['available'],
                'priority': provider['priority'],
                'error_count': provider['error_count'],
                'consecutive_failures': provider['consecutive_failures'],
                'last_success': provider.get('last_success'),
                'max_errors': provider['max_errors'],
                'model': provider.get('model', 'N/A'),
                'enabled': provider.get('enabled', True)
            }

        return status

    def generate_content(self, prompt: str, max_tokens: int = 1000, **kwargs) -> Optional[str]:
        """Método alias para compatibilidade"""
        provider = kwargs.get('provider')
        return self.generate_analysis(prompt, max_tokens, provider)

    # Método adicionado para compatibilidade com Mental Drivers Architect
    def gerar_resposta_inteligente(self, prompt: str, modelo_preferido: str = 'gemini', max_tentativas: int = 2) -> Dict[str, Any]:
        """Método compatível com o Mental Drivers Architect"""
        try:
            # O prompt deve ser passado para generate_response
            # As configurações de max_tokens e temperature podem ser passadas via kwargs em generate_response
            response_data = self.generate_response(prompt=prompt, max_tokens=4000, temperature=0.7) # Ajustado para usar generate_response

            if response_data and response_data.get('success'):
                return {
                    'response': response_data.get('content'),
                    'modelo_usado': response_data.get('provider', modelo_preferido),
                    'success': True
                }
            else:
                return {
                    'error': response_data.get('error', 'Falha desconhecida na geração'),
                    'success': False
                }

        except Exception as e:
            logger.error(f"❌ Erro em gerar_resposta_inteligente: {e}")
            return {
                'error': str(e),
                'success': False
            }


# Instância global
ai_manager = AIManager()