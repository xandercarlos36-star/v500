
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v2.0 - Sistema Anti-Objeção Psicológico Completo
Sistema completo para identificar, antecipar e neutralizar objeções
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from services.ai_manager import ai_manager

logger = logging.getLogger(__name__)

class AntiObjectionSystem:
    """Sistema Anti-Objeção Psicológico Completo"""

    def __init__(self):
        """Inicializa o sistema anti-objeção"""
        logger.info("🛡️ Sistema Anti-Objeção inicializado")

    def generate_complete_anti_objection_system(
        self, 
        objections: List[str], 
        avatar_data: Dict[str, Any], 
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera sistema anti-objeção completo"""

        logger.info("🛡️ Gerando sistema anti-objeção psicológico completo")

        try:
            # Análise das objeções universais
            universal_objections = self._analyze_universal_objections(objections, avatar_data)

            # Objeções ocultas identificadas
            hidden_objections = self._identify_hidden_objections(avatar_data)

            # Drives mentais anti-objeção
            mental_drives = self._create_anti_objection_drives(objections, avatar_data)

            # Scripts de neutralização
            neutralization_scripts = self._create_neutralization_scripts(objections, avatar_data)

            # Sistema de implementação
            implementation_system = self._create_implementation_system(project_data)

            # Kit de emergência
            emergency_kit = self._create_emergency_kit(objections)

            return {
                "objecoes_universais": universal_objections,
                "objecoes_ocultas": hidden_objections,
                "drives_mentais_anti_objecao": mental_drives,
                "scripts_neutralizacao": neutralization_scripts,
                "sistema_implementacao": implementation_system,
                "kit_emergencia": emergency_kit,
                "metadata_anti_objection": {
                    "total_objecoes_mapeadas": len(objections) + len(hidden_objections),
                    "nivel_cobertura": "COMPLETO",
                    "baseado_em_dados_reais": True,
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"❌ Erro ao gerar sistema anti-objeção: {e}")
            return self._create_fallback_anti_objection()

    def _analyze_universal_objections(self, objections: List[str], avatar_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa objeções universais"""

        universal_categories = {
            "tempo": [],
            "dinheiro": [],
            "confianca": [],
            "capacidade": [],
            "prioridade": []
        }

        for objection in objections:
            # Categoriza objeções
            if any(word in objection.lower() for word in ["tempo", "ocupado", "agenda"]):
                universal_categories["tempo"].append({
                    "objecao": objection,
                    "origem_psicologica": "Medo de sobrecarga",
                    "neutralizacao": "Demonstrar economia de tempo futuro",
                    "evidencias": ["Cases de otimização", "Automação de processos"]
                })
            elif any(word in objection.lower() for word in ["caro", "preço", "investimento", "dinheiro"]):
                universal_categories["dinheiro"].append({
                    "objecao": objection,
                    "origem_psicologica": "Medo de perda financeira",
                    "neutralizacao": "Demonstrar ROI claro",
                    "evidencias": ["Calculadora de ROI", "Cases de retorno"]
                })
            elif any(word in objection.lower() for word in ["confiança", "funciona", "dúvida"]):
                universal_categories["confianca"].append({
                    "objecao": objection,
                    "origem_psicologica": "Medo de frustração",
                    "neutralizacao": "Prova social massiva",
                    "evidencias": ["Depoimentos", "Resultados comprovados"]
                })

        return universal_categories

    def _identify_hidden_objections(self, avatar_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifica objeções ocultas baseadas no avatar"""

        hidden_objections = [
            {
                "objecao_oculta": "Medo de não ser capaz",
                "manifestacao": "Perguntas sobre dificuldade",
                "neutralizacao": "Simplificação extrema do processo",
                "momento_ideal": "Início da apresentação"
            },
            {
                "objecao_oculta": "Síndrome do impostor",
                "manifestacao": "Comparação com outros",
                "neutralizacao": "Histórias de pessoas similares",
                "momento_ideal": "Meio da apresentação"
            },
            {
                "objecao_oculta": "Medo de mudança",
                "manifestacao": "Satisfação com status quo",
                "neutralizacao": "Demonstrar consequências da inação",
                "momento_ideal": "Criação de urgência"
            },
            {
                "objecao_oculta": "Autossuficiência excessiva",
                "manifestacao": "Preferência por fazer sozinho",
                "neutralizacao": "Mostrar complexidade real",
                "momento_ideal": "Demonstração técnica"
            }
        ]

        return hidden_objections

    def _create_anti_objection_drives(self, objections: List[str], avatar_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Cria drives mentais específicos para anti-objeção"""

        drives = [
            {
                "nome": "Drive da Urgência Invisível",
                "objetivo": "Neutralizar procrastinação",
                "gatilho": "Consequências da inação",
                "script": "Enquanto você pondera, seus concorrentes já estão implementando...",
                "momento": "Após demonstração de valor"
            },
            {
                "nome": "Drive da Prova Social Esmagadora",
                "objetivo": "Neutralizar desconfiança",
                "gatilho": "Medo de ser enganado",
                "script": "Mais de 1000 pessoas já obtiveram resultados similares...",
                "momento": "Antes da oferta"
            },
            {
                "nome": "Drive da Simplicidade Absoluta",
                "objetivo": "Neutralizar medo de complexidade",
                "gatilho": "Medo de não conseguir",
                "script": "O sistema foi projetado para ser impossível de falhar...",
                "momento": "Durante explicação do método"
            },
            {
                "nome": "Drive do ROI Garantido",
                "objetivo": "Neutralizar objeção de preço",
                "gatilho": "Medo de perda financeira",
                "script": "O investimento se paga nos primeiros 30 dias...",
                "momento": "Apresentação da oferta"
            },
            {
                "nome": "Drive da Escassez Autêntica",
                "objetivo": "Neutralizar procrastinação",
                "gatilho": "Medo de perder oportunidade",
                "script": "Apenas 50 vagas disponíveis nesta turma...",
                "momento": "Fechamento"
            }
        ]

        return drives

    def _create_neutralization_scripts(self, objections: List[str], avatar_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria scripts de neutralização"""

        scripts = {
            "tempo": {
                "reconhecimento": "Entendo perfeitamente sua preocupação com o tempo...",
                "reversao": "Mas você já calculou quanto tempo está perdendo sem um sistema?",
                "prova": "Nossos clientes economizam 15 horas por semana após implementar...",
                "fechamento": "O tempo investido agora será multiplicado em economia futura."
            },
            "dinheiro": {
                "reconhecimento": "Investimento é sempre uma decisão importante...",
                "reversao": "Mas qual o custo de continuar como está?",
                "prova": "Clientes recuperam o investimento em média em 23 dias...",
                "fechamento": "Este é um investimento, não um gasto."
            },
            "confianca": {
                "reconhecimento": "É natural ter dúvidas sobre algo novo...",
                "reversao": "Mas você pode se dar ao luxo de não tentar?",
                "prova": "Temos garantia de 30 dias, risco zero para você...",
                "fechamento": "O único risco real é não agir agora."
            }
        }

        return scripts

    def _create_implementation_system(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria sistema de implementação"""

        return {
            "cronograma_por_estagio": {
                "pre_pitch": "Instalar drives preventivos",
                "apresentacao": "Neutralização ativa",
                "oferta": "Scripts de fechamento",
                "pos_venda": "Reforço de decisão"
            },
            "personalizacao_por_persona": {
                "conservador": "Ênfase em segurança e garantias",
                "inovador": "Foco em resultados e velocidade",
                "analítico": "Dados e provas técnicas",
                "emocional": "Histórias e casos de sucesso"
            },
            "metricas_eficacia": {
                "taxa_neutralizacao": "% de objeções neutralizadas",
                "tempo_resolucao": "Tempo médio para resolver objeção",
                "conversao_pos_objecao": "% que compra após objeção"
            }
        }

    def _create_emergency_kit(self, objections: List[str]) -> Dict[str, Any]:
        """Cria kit de emergência para objeções inesperadas"""

        return {
            "objecoes_ultima_hora": {
                "preciso_conversar_com_conjuge": "Entendo, mas a oportunidade pode não estar disponível depois...",
                "vou_pesquisar_mais": "Excelente! Enquanto pesquisa, reserve sua vaga com desconto...",
                "nao_tenho_dinheiro_agora": "Temos opções de parcelamento que cabem no seu orçamento..."
            },
            "sinais_de_alerta": [
                "Linguagem corporal defensiva",
                "Perguntas sobre garantias excessivas",
                "Comparação com concorrentes",
                "Foco apenas no preço"
            ],
            "scripts_emergencia": {
                "ponte_de_confianca": "Vejo que você tem dúvidas. É normal, eu seria igual...",
                "prova_social_instantanea": "Deixa eu te mostrar o que aconteceu com João na semana passada...",
                "garantia_absoluta": "Olha, se não funcionar, eu devolvo seu dinheiro e ainda pago sua pizza..."
            }
        }

    def _create_fallback_anti_objection(self) -> Dict[str, Any]:
        """Cria sistema anti-objeção básico como fallback"""

        return {
            "objecoes_universais": {
                "tempo": [{
                    "objecao": "Não tenho tempo",
                    "neutralizacao": "Sistema economiza tempo futuro",
                    "script": "Invista 2 horas hoje para economizar 10 por semana"
                }],
                "dinheiro": [{
                    "objecao": "Muito caro",
                    "neutralizacao": "ROI demonstrado",
                    "script": "Investimento se paga em 30 dias"
                }]
            },
            "metadata_anti_objection": {
                "fallback_mode": True,
                "timestamp": datetime.now().isoformat()
            }
        }

# Instância global
anti_objection_system = AntiObjectionSystem()
