# Instagram Graph API - Notas de Implementação

## Business Discovery API

A API Business Discovery permite obter dados de outros perfis Business/Creator do Instagram.

### Endpoint

```
GET /<IG_USER_ID>?fields=business_discovery.username(<USERNAME>)
```

### Campos Disponíveis

- `followers_count` - Número de seguidores
- `media_count` - Número de posts
- `media` - Edge para acessar mídias do perfil

### Campos de Mídia

- `comments_count` - Número de comentários
- `like_count` - Número de curtidas
- `view_count` - Visualizações (para vídeos/reels)

### Exemplo de Request

```
GET graph.facebook.com
  /17841405309211844
    ?fields=business_discovery.username(bluebottle){followers_count,media_count,media{comments_count,like_count}}
```

### Permissões Necessárias

- `instagram_basic`
- `instagram_manage_insights`
- `pages_read_engagement`

### Limitações

- Só funciona para perfis Business ou Creator (não funciona para perfis pessoais)
- Perfis com restrição de idade não retornam dados
- Necessário conhecer o username do perfil alvo

## Hashtag Search API

Para buscar por hashtags, usar o endpoint IG Hashtag Search.

### Endpoint

```
GET /<IG_USER_ID>/hashtag_search?user_id={user-id}&q={hashtag}
```

Retorna o ID da hashtag que pode ser usado para buscar mídias recentes.

### Recent Media por Hashtag

```
GET /<HASHTAG_ID>/recent_media?user_id={user-id}
```

Retorna mídias recentes com a hashtag especificada.
