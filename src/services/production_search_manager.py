#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v2.0 - Production Search Manager
Gerenciador de busca para produção com múltiplos provedores e fallbacks
"""

import os
import logging
import time
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import json
import random
from services.exa_client import exa_client
from datetime import datetime

logger = logging.getLogger(__name__)

class ProductionSearchManager:
    """Gerenciador de busca para produção com sistema de fallback"""

    def __init__(self):
        """Inicializa o gerenciador de busca"""
        self.providers = {
            'exa': {
                'enabled': exa_client.is_available(),
                'priority': 1,  # Prioridade máxima
                'error_count': 0,
                'max_errors': 3,
                'client': exa_client
            },
            'google': {
                'enabled': bool(os.getenv('GOOGLE_SEARCH_KEY') and os.getenv('GOOGLE_CSE_ID')),
                'priority': 2,
                'error_count': 0,
                'max_errors': 3,
                'api_key': os.getenv('GOOGLE_SEARCH_KEY'),
                'cse_id': os.getenv('GOOGLE_CSE_ID'),
                'base_url': 'https://www.googleapis.com/customsearch/v1'
            },
            'serper': {
                'enabled': bool(os.getenv('SERPER_API_KEY')),
                'priority': 3,
                'error_count': 0,
                'max_errors': 3,
                'api_key': os.getenv('SERPER_API_KEY'),
                'base_url': 'https://google.serper.dev/search'
            },
            'bing': {
                'enabled': True,  # Sempre disponível via scraping
                'priority': 4,
                'error_count': 0,
                'max_errors': 5,
                'base_url': 'https://www.bing.com/search'
            }
            # DuckDuckGo removido para otimização de performance e qualidade
        }

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive'
        }

        self.cache = {}
        self.cache_ttl = 3600  # 1 hora

        enabled_count = sum(1 for p in self.providers.values() if p['enabled'])
        logger.info(f"Production Search Manager inicializado com {enabled_count} provedores")

    def search_with_fallback(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Realiza busca com sistema de fallback automático"""

        # Verifica cache primeiro
        cache_key = f"{query}_{max_results}"
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            if time.time() - cache_data['timestamp'] < self.cache_ttl:
                logger.info(f"🔄 Resultado do cache para: {query}")
                return cache_data['results']

        # Busca com fallback
        for provider_name in self._get_provider_order():
            if not self._is_provider_available(provider_name):
                continue

            try:
                logger.info(f"🔍 Buscando com {provider_name}: {query}")

                if provider_name == 'google':
                    results = self._search_google(query, max_results)
                elif provider_name == 'serper':
                    results = self._search_serper(query, max_results)
                elif provider_name == 'bing':
                    results = self._search_bing(query, max_results)
                elif provider_name == 'exa': # Adicionado busca Exa
                    results = self._search_exa(query, max_results)
                else:
                    continue

                if results:
                    # Cache resultado
                    self.cache[cache_key] = {
                        'results': results,
                        'timestamp': time.time(),
                        'provider': provider_name
                    }

                    logger.info(f"✅ {provider_name}: {len(results)} resultados")
                    return results
                else:
                    logger.warning(f"⚠️ {provider_name}: 0 resultados")

            except Exception as e:
                logger.error(f"❌ Erro em {provider_name}: {str(e)}")
                self._record_provider_error(provider_name)
                continue

        logger.error("❌ Todos os provedores de busca falharam")
        return []

    def _get_provider_order(self) -> List[str]:
        """Retorna provedores ordenados por prioridade"""
        available_providers = [
            (name, provider) for name, provider in self.providers.items()
            if self._is_provider_available(name)
        ]

        # Ordena por prioridade e número de erros
        available_providers.sort(key=lambda x: (x[1]['priority'], x[1]['error_count']))

        return [name for name, _ in available_providers]

    def _is_provider_available(self, provider_name: str) -> bool:
        """Verifica se provedor está disponível"""
        provider = self.providers.get(provider_name, {})
        return (provider.get('enabled', False) and 
                provider.get('error_count', 0) < provider.get('max_errors', 3))

    def _record_provider_error(self, provider_name: str):
        """Registra erro do provedor"""
        if provider_name in self.providers:
            self.providers[provider_name]['error_count'] += 1

            if self.providers[provider_name]['error_count'] >= self.providers[provider_name]['max_errors']:
                logger.warning(f"⚠️ Provedor {provider_name} desabilitado temporariamente")

    def _search_google(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Busca usando Google Custom Search API"""
        provider = self.providers['google']

        params = {
            'key': provider['api_key'],
            'cx': provider['cse_id'],
            'q': query,
            'num': min(max_results, 10),
            'lr': 'lang_pt',
            'gl': 'br',
            'safe': 'off'
        }

        response = requests.get(
            provider['base_url'],
            params=params,
            headers=self.headers,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            results = []

            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': 'google'
                })

            return results
        else:
            raise Exception(f"Google API retornou status {response.status_code}")

    def _search_serper(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Busca usando Serper API"""
        provider = self.providers['serper']

        headers = {
            **self.headers,
            'X-API-KEY': provider['api_key'],
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'gl': 'br',
            'hl': 'pt',
            'num': max_results
        }

        response = requests.post(
            provider['base_url'],
            json=payload,
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            results = []

            for item in data.get('organic', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': 'serper'
                })

            return results
        else:
            raise Exception(f"Serper API retornou status {response.status_code}")

    def _search_bing(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Busca usando Bing (scraping)"""
        search_url = f"{self.providers['bing']['base_url']}?q={quote_plus(query)}&cc=br&setlang=pt-br&count={max_results}"

        response = requests.get(search_url, headers=self.headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []

            result_items = soup.find_all('li', class_='b_algo')

            for item in result_items[:max_results]:
                title_elem = item.find('h2')
                if title_elem:
                    link_elem = title_elem.find('a')
                    if link_elem:
                        title = title_elem.get_text(strip=True)
                        url = link_elem.get('href', '')

                        snippet_elem = item.find('p')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                        if url and title and url.startswith('http'):
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet,
                                'source': 'bing'
                            })

            return results
        else:
            raise Exception(f"Bing retornou status {response.status_code}")

    # MÉTODO _search_duckduckgo REMOVIDO CONFORME PLANO DE OTIMIZAÇÃO
    # DuckDuckGo foi removido para melhorar performance e qualidade dos resultados

    def _placeholder_removed_duckduckgo(self):
        pass

    def get_provider_status(self) -> Dict[str, Any]:
        """Retorna status de todos os provedores"""
        status = {}

        for name, provider in self.providers.items():
            status[name] = {
                'enabled': provider['enabled'],
                'available': self._is_provider_available(name),
                'priority': provider['priority'],
                'error_count': provider['error_count'],
                'max_errors': provider['max_errors']
            }

        return status

    def reset_provider_errors(self, provider_name: str = None):
        """Reset contadores de erro dos provedores"""
        if provider_name:
            if provider_name in self.providers:
                self.providers[provider_name]['error_count'] = 0
                logger.info(f"🔄 Reset erros do provedor: {provider_name}")
        else:
            for provider in self.providers.values():
                provider['error_count'] = 0
            logger.info("🔄 Reset erros de todos os provedores")

    def clear_cache(self):
        """Limpa cache de busca"""
        self.cache = {}
        logger.info("🧹 Cache de busca limpo")

    def test_provider(self, provider_name: str) -> bool:
        """Testa um provedor específico"""
        if provider_name not in self.providers:
            return False

        try:
            test_query = "teste mercado digital Brasil 2024" # Query de teste melhorada

            if provider_name == 'google':
                results = self._search_google(test_query, 3)
            elif provider_name == 'serper':
                results = self._search_serper(test_query, 3)
            elif provider_name == 'bing':
                results = self._search_bing(test_query, 3)
            elif provider_name == 'exa': # Teste para Exa
                results = self._search_exa(test_query, 3)
            else:
                return False

            return len(results) > 0

        except Exception as e:
            logger.error(f"❌ Teste do provedor {provider_name} falhou: {e}")
            return False

    def _search_exa(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Busca usando Exa Neural Search"""
        try:
            # Melhora query para mercado brasileiro e aumento de robustez/espectro
            enhanced_query = self._enhance_query_for_brazil(query)
            enhanced_query += " " + self._get_broad_search_terms() # Adiciona termos amplos

            # Domínios brasileiros preferenciais
            include_domains = [
                "g1.globo.com", "exame.com", "valor.globo.com", "estadao.com.br",
                "folha.uol.com.br", "canaltech.com.br", "infomoney.com.br", "techtudo.com.br",
                "adrenaline.com.br", "tecnologia.uol.com.br", "olhardigital.com.br",
                "computerworld.com.br", "idg.com.br", "canalrural.com.br", "agrobase.com.br",
                "ruralverde.com.br", "agrolink.com.br", "revistagloborural.globo.com",
                "dinheirorural.com.br", "campo.aesc.com.br"
            ]

            # Aumenta o espectro de datas e usa autoprompt
            exa_response = exa_client.search(
                query=enhanced_query,
                num_results=max_results,
                include_domains=include_domains,
                start_published_date="2022-01-01", # Amplia para 2022
                end_published_date=time.strftime("%Y-%m-%d"), # Data atual
                use_autoprompt=True, # Mantém autoprompt
                type="neural"
            )

            if not exa_response or 'results' not in exa_response:
                raise Exception("Exa não retornou resultados válidos")

            results = []
            for item in exa_response['results']:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'snippet': item.get('text', '')[:500], # Aumenta tamanho do snippet
                    'source': 'exa',
                    'score': item.get('score', 0),
                    'published_date': item.get('publishedDate', ''),
                    'exa_id': item.get('id', '')
                })

            logger.info(f"✅ Exa Neural Search: {len(results)} resultados")
            return results

        except Exception as e:
            if "quota" in str(e).lower() or "limit" in str(e).lower():
                logger.warning(f"⚠️ Exa atingiu limite: {str(e)}")
            # Registra erro se Exa falhar
            self._record_provider_error('exa')
            raise e

    def _enhance_query_for_brazil(self, query: str) -> str:
        """Melhora query para pesquisa no Brasil"""
        enhanced_query = query
        query_lower = query.lower()

        # Adiciona termos brasileiros se não estiverem presentes
        if not any(term in query_lower for term in ["brasil", "brasileiro", "br", "brazil"]):
            enhanced_query += " Brasil"

        # Adiciona ano atual se não estiver presente
        current_year = time.strftime("%Y")
        if not any(year in query for year in [current_year, str(int(current_year) - 1)]):
            enhanced_query += f" {current_year}"

        # Remove termos duplicados e ajusta espaçamento
        return " ".join(dict.fromkeys(enhanced_query.split())).strip()

    def _get_broad_search_terms(self) -> str:
        """Retorna termos para aumentar o espectro da pesquisa"""
        return "mercado digital tecnologia inovação investimento finanças economia setor"

    def comprehensive_search(self, query: str, num_results: int = 15) -> Dict[str, Any]:
        """Busca abrangente usando múltiplas fontes com estratégia otimizada"""
        try:
            logger.info(f"🔍 Iniciando busca comprehensive para: {query}")

            all_results = []
            search_sources = []
            errors = []

            # 1. Exa Search (neural) - Prioridade alta
            try:
                logger.info("🧠 Tentando busca neural Exa...")
                exa_results = self.exa_client.search_comprehensive(
                    query, 
                    num_results=min(8, num_results),
                    min_length=300,
                    max_length=2000
                )

                if exa_results.get('success') and exa_results.get('results'):
                    valid_exa = [r for r in exa_results['results'] if len(r.get('text', '')) > 100]
                    all_results.extend(valid_exa)
                    search_sources.append(f'exa({len(valid_exa)})')
                    logger.info(f"✅ Exa: {len(valid_exa)} resultados válidos")
                else:
                    errors.append(f"Exa: {exa_results.get('error', 'Sem resultados')}")

            except Exception as e:
                error_msg = f"Exa falhou: {str(e)[:100]}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")

            # 2. Google Custom Search - Se Exa não trouxe resultados suficientes
            if len(all_results) < num_results // 2:
                try:
                    logger.info("🔍 Complementando com Google Search...")
                    google_results = self.google_search(query, num_results=min(7, num_results))

                    if google_results.get('success') and google_results.get('results'):
                        valid_google = [r for r in google_results['results'] if r.get('url')]
                        all_results.extend(valid_google)
                        search_sources.append(f'google({len(valid_google)})')
                        logger.info(f"✅ Google: {len(valid_google)} resultados")
                    else:
                        errors.append(f"Google: {google_results.get('error', 'Sem resultados')}")

                except Exception as e:
                    error_msg = f"Google falhou: {str(e)[:100]}"
                    errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")

            # 3. Serper API - Como última opção ou complemento
            if len(all_results) < num_results // 3:
                try:
                    logger.info("🔍 Complementando com Serper...")
                    serper_results = self.serper_search(query, num_results=min(5, num_results))

                    if serper_results.get('success') and serper_results.get('results'):
                        valid_serper = [r for r in serper_results['results'] if r.get('url')]
                        all_results.extend(valid_serper)
                        search_sources.append(f'serper({len(valid_serper)})')
                        logger.info(f"✅ Serper: {len(valid_serper)} resultados")
                    else:
                        errors.append(f"Serper: {serper_results.get('error', 'Sem resultados')}")

                except Exception as e:
                    error_msg = f"Serper falhou: {str(e)[:100]}"
                    errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")

            # Processamento final dos resultados
            if all_results:
                # Remove duplicatas por URL
                unique_results = self._remove_duplicates_advanced(all_results)

                # Enriquece resultados com scores
                enriched_results = self._enrich_results_with_scores(unique_results, query)

                # Ordena por relevância combinada
                sorted_results = self._sort_by_comprehensive_score(enriched_results)

                final_results = sorted_results[:num_results]

                logger.info(f"✅ Busca comprehensive concluída: {len(final_results)} resultados finais")

                return {
                    'success': True,
                    'query': query,
                    'total_results': len(final_results),
                    'results': final_results,
                    'sources_used': search_sources,
                    'errors': errors if errors else None,
                    'search_strategy': 'comprehensive_multi_source',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning(f"⚠️ Nenhum resultado encontrado para: {query}")
                return {
                    'success': False,
                    'query': query,
                    'total_results': 0,
                    'results': [],
                    'sources_used': search_sources,
                    'errors': errors,
                    'error': 'Nenhuma fonte retornou resultados válidos'
                }

        except Exception as e:
            logger.error(f"❌ Erro crítico na busca comprehensive: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'results': [],
                'sources_used': [],
                'errors': [f"Erro crítico: {str(e)}"]
            }

    def _remove_duplicates_advanced(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicatas avançadas por URL e similaridade de conteúdo"""
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get('url', '').lower().strip()
            if url and url not in seen_urls:
                # Normaliza URL removendo parâmetros comuns
                normalized_url = url.split('?')[0].split('#')[0]
                if normalized_url not in seen_urls:
                    seen_urls.add(url)
                    seen_urls.add(normalized_url)
                    unique_results.append(result)

        return unique_results

    def _enrich_results_with_scores(self, results: List[Dict], query: str) -> List[Dict]:
        """Enriquece resultados com scores de relevância"""
        query_terms = set(query.lower().split())

        for result in results:
            relevance_score = 0

            # Score baseado no título
            title = result.get('title', '').lower()
            title_matches = sum(1 for term in query_terms if term in title)
            relevance_score += title_matches * 3

            # Score baseado no texto
            text = result.get('text', '').lower()
            text_matches = sum(1 for term in query_terms if term in text)
            relevance_score += text_matches

            # Score baseado na fonte
            source = result.get('source', '')
            if source == 'exa_neural':
                relevance_score += 2  # Bonus para busca neural

            # Score baseado no tamanho do conteúdo
            content_length = len(result.get('text', ''))
            if content_length > 500:
                relevance_score += 1

            result['comprehensive_score'] = relevance_score
            result['content_quality'] = min(100, content_length // 10)

        return results

    def _sort_by_comprehensive_score(self, results: List[Dict]) -> List[Dict]:
        """Ordena por score abrangente combinando múltiplos fatores"""
        return sorted(
            results, 
            key=lambda x: (
                x.get('comprehensive_score', 0),
                x.get('score', 0),
                x.get('content_quality', 0),
                len(x.get('text', ''))
            ), 
            reverse=True
        )

# Instância global
production_search_manager = ProductionSearchManager()