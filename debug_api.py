#!/usr/bin/env python3
"""
Script de debug para investigar estrutura das respostas das APIs.
"""

import sys
import json

sys.path.append('/opt/.manus/.sandbox-runtime')

def debug_tiktok():
    """Debug da API TikTok."""
    print("=" * 60)
    print("DEBUG: TikTok Search API")
    print("=" * 60)
    
    from data_api import ApiClient
    client = ApiClient()
    
    response = client.call_api(
        'Tiktok/search_tiktok_video_general',
        query={'keyword': 'emagrecimento'}
    )
    
    # Salvar resposta completa
    with open('/home/ubuntu/voy-influencer-prospector/data/debug_tiktok.json', 'w') as f:
        json.dump(response, f, indent=2, ensure_ascii=False)
    
    print(f"Resposta salva em data/debug_tiktok.json")
    
    if response:
        print(f"\nChaves principais: {list(response.keys())}")
        
        if 'data' in response:
            videos = response.get('data', [])
            print(f"Número de vídeos: {len(videos)}")
            
            if videos:
                first = videos[0]
                print(f"\nChaves do primeiro vídeo: {list(first.keys())}")
                
                author = first.get('author', {})
                print(f"\nDados do autor:")
                print(f"  uniqueId: {author.get('uniqueId', 'N/A')}")
                print(f"  nickname: {author.get('nickname', 'N/A')}")
                print(f"  id: {author.get('id', 'N/A')}")
                
                author_stats = first.get('authorStats', {})
                print(f"\nEstatísticas do autor:")
                print(f"  followerCount: {author_stats.get('followerCount', 'N/A')}")
                print(f"  heartCount: {author_stats.get('heartCount', 'N/A')}")
                print(f"  videoCount: {author_stats.get('videoCount', 'N/A')}")


def debug_youtube():
    """Debug da API YouTube."""
    print("\n" + "=" * 60)
    print("DEBUG: YouTube Search API")
    print("=" * 60)
    
    from data_api import ApiClient
    client = ApiClient()
    
    response = client.call_api(
        'Youtube/search',
        query={'q': 'emagrecimento antes e depois', 'hl': 'pt', 'gl': 'BR'}
    )
    
    # Salvar resposta completa
    with open('/home/ubuntu/voy-influencer-prospector/data/debug_youtube.json', 'w') as f:
        json.dump(response, f, indent=2, ensure_ascii=False)
    
    print(f"Resposta salva em data/debug_youtube.json")
    
    if response:
        print(f"\nChaves principais: {list(response.keys())}")
        
        if 'contents' in response:
            contents = response.get('contents', [])
            print(f"Número de resultados: {len(contents)}")
            
            if contents:
                first = contents[0]
                print(f"\nChaves do primeiro resultado: {list(first.keys())}")
                print(f"Tipo: {first.get('type', 'N/A')}")
                
                if first.get('type') == 'video':
                    video = first.get('video', {})
                    print(f"\nDados do vídeo:")
                    print(f"  title: {video.get('title', 'N/A')[:50]}")
                    print(f"  channelId: {video.get('channelId', 'N/A')}")
                    print(f"  channelTitle: {video.get('channelTitle', 'N/A')}")


def main():
    debug_tiktok()
    debug_youtube()
    
    print("\n" + "=" * 60)
    print("Debug concluído! Verifique os arquivos JSON em data/")
    print("=" * 60)


if __name__ == "__main__":
    main()
