#!/usr/bin/env python3
"""
Script de debug para verificar dados retornados da API do Instagram.
"""

import os
import requests
import json

INSTAGRAM_API_BASE = "https://graph.facebook.com/v18.0"

token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
user_id = os.environ.get("INSTAGRAM_USER_ID")

print(f"Token: {token[:20]}..." if token else "Token não configurado!")
print(f"User ID: {user_id}")

# Testar alguns perfis conhecidos
test_profiles = [
    "thaiscarla",
    "alexandrismos",
    "flufranco",
    "niinasecrets",
]

for username in test_profiles:
    print(f"\n{'='*50}")
    print(f"Testando: @{username}")
    
    url = f"{INSTAGRAM_API_BASE}/{user_id}"
    params = {
        "fields": f"business_discovery.username({username}){{username,name,biography,followers_count,media_count,media{{like_count,comments_count}}}}",
        "access_token": token
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            business = data.get("business_discovery", {})
            
            if business:
                print(f"  Nome: {business.get('name')}")
                print(f"  Seguidores: {business.get('followers_count', 0):,}")
                print(f"  Posts: {business.get('media_count', 0)}")
                
                # Calcular engajamento
                media = business.get("media", {}).get("data", [])
                if media:
                    total_eng = sum(m.get("like_count", 0) + m.get("comments_count", 0) for m in media[:10])
                    avg_eng = total_eng / len(media[:10])
                    followers = business.get("followers_count", 1)
                    eng_rate = (avg_eng / followers) * 100
                    print(f"  Engajamento médio: {eng_rate:.2f}%")
                    print(f"  Likes/Comments últimos posts: {[m.get('like_count', 0) for m in media[:5]]}")
                
                bio = business.get("biography", "")[:100]
                print(f"  Bio: {bio}...")
            else:
                print("  Perfil não encontrado ou privado")
        else:
            print(f"  Erro: {response.text[:200]}")
            
    except Exception as e:
        print(f"  Exceção: {e}")

print("\n" + "="*50)
print("Debug concluído!")
