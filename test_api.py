#!/usr/bin/env python3
"""
Script de teste para validar as APIs disponíveis.
"""

import sys
import json
import time

sys.path.append('/opt/.manus/.sandbox-runtime')

def test_tiktok_search():
    """Testa busca no TikTok."""
    print("Testando TikTok Search...")
    
    try:
        from data_api import ApiClient
        client = ApiClient()
        
        response = client.call_api(
            'Tiktok/search_tiktok_video_general',
            query={'keyword': 'emagrecimento'}
        )
        
        if response and 'data' in response:
            videos = response.get('data', [])
            print(f"  ✅ TikTok: {len(videos)} vídeos encontrados")
            
            # Mostrar primeiro resultado
            if videos:
                first = videos[0]
                author = first.get('author', {})
                print(f"  Primeiro autor: @{author.get('uniqueId', 'N/A')}")
                print(f"  Nickname: {author.get('nickname', 'N/A')}")
                
                author_stats = first.get('authorStats', {})
                print(f"  Seguidores: {author_stats.get('followerCount', 0):,}")
            
            return True
        else:
            print(f"  ❌ TikTok: Resposta vazia ou inválida")
            return False
            
    except Exception as e:
        print(f"  ❌ TikTok: Erro - {e}")
        return False


def test_youtube_search():
    """Testa busca no YouTube."""
    print("\nTestando YouTube Search...")
    
    try:
        from data_api import ApiClient
        client = ApiClient()
        
        response = client.call_api(
            'Youtube/search',
            query={
                'q': 'emagrecimento antes e depois',
                'hl': 'pt',
                'gl': 'BR'
            }
        )
        
        if response and 'contents' in response:
            contents = response.get('contents', [])
            print(f"  ✅ YouTube: {len(contents)} resultados encontrados")
            
            # Contar tipos
            videos = sum(1 for c in contents if c.get('type') == 'video')
            channels = sum(1 for c in contents if c.get('type') == 'channel')
            print(f"  Vídeos: {videos}, Canais: {channels}")
            
            return True
        else:
            print(f"  ❌ YouTube: Resposta vazia ou inválida")
            return False
            
    except Exception as e:
        print(f"  ❌ YouTube: Erro - {e}")
        return False


def test_tiktok_user_info():
    """Testa obter info de usuário TikTok."""
    print("\nTestando TikTok User Info...")
    
    try:
        from data_api import ApiClient
        client = ApiClient()
        
        response = client.call_api(
            'Tiktok/get_user_info',
            query={'uniqueId': 'charlidamelio'}
        )
        
        if response and 'userInfo' in response:
            user_info = response.get('userInfo', {})
            user = user_info.get('user', {})
            stats = user_info.get('stats', {})
            
            print(f"  ✅ TikTok User Info funcionando")
            print(f"  Usuário: @{user.get('uniqueId', 'N/A')}")
            print(f"  Seguidores: {stats.get('followerCount', 0):,}")
            print(f"  Verificado: {user.get('verified', False)}")
            
            return True
        else:
            print(f"  ❌ TikTok User Info: Resposta inválida")
            return False
            
    except Exception as e:
        print(f"  ❌ TikTok User Info: Erro - {e}")
        return False


def main():
    """Executa todos os testes."""
    print("=" * 50)
    print("TESTE DE APIs")
    print("=" * 50)
    
    results = {
        'tiktok_search': test_tiktok_search(),
        'youtube_search': test_youtube_search(),
        'tiktok_user_info': test_tiktok_user_info(),
    }
    
    print("\n" + "=" * 50)
    print("RESUMO")
    print("=" * 50)
    
    for api, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {api}")
    
    total_success = sum(results.values())
    print(f"\nTotal: {total_success}/{len(results)} APIs funcionando")
    
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
