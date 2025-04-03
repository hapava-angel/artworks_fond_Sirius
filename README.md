В ветке master лежит музейный гид по виртуальному выставочному фонду at the ОЦ «Сириус», готовый для деплоя. 
Для запсука требуется установить docker. Команда для запуска проекта: docker compose up --build -d 

# ИИ-гид

## Scheme

```mermaid
graph LR
    teleram_bot
    subgraph generation
        gen[GigaChat]
        db[database]
        gener[GigaChat-Max]
        gen <-.-> db
    end
    subgraph validation
        val[GigaChat-Max-Eval]
    end
    teleram_bot ---> gen
    gen --> val
    val --> gener
    gener ---> teleram_bot
```
