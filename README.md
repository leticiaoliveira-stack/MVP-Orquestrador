# Orquestrador Pedagógico — versão para nuvem

Esta versão foi preparada para rodar **sem instalar Python no computador**.

## Caminho recomendado: Streamlit Community Cloud

Você usa o Orquestrador pelo navegador. O Python roda na nuvem.

### Arquivos que devem ir para o GitHub

- `streamlit_app.py`
- `requirements.txt`

### Publicação

1. Crie um repositório no GitHub.
2. Envie os dois arquivos acima para o repositório.
3. Entre em `https://share.streamlit.io`.
4. Faça login com GitHub.
5. Clique em **Create app**.
6. Escolha o repositório.
7. Em **Main file path**, informe:
   `streamlit_app.py`
8. Abra **Advanced settings**.
9. Em **Secrets**, coloque:

```toml
OPENAI_API_KEY = "SUA_CHAVE_AQUI"
```

10. Clique em **Deploy**.

Depois disso, o Orquestrador ficará disponível em um endereço `*.streamlit.app`.

## Importante

- Não coloque sua chave da OpenAI dentro do arquivo Python ou no GitHub.
- A chave deve ficar apenas em **Secrets**.
- O uso da API da OpenAI é cobrado separadamente da assinatura do ChatGPT.
- Este MVP usa upload manual dos documentos. A próxima versão pode consultar uma base no Google Drive.

## Teste UCA

Preencha:
- curso;
- disciplina;
- carga horária;
- créditos;
- período/trimestre.

Envie:
- matriz curricular;
- perfil do egresso;
- DCNs;
- matriz de referência do ENADE.

## Teste U4

Preencha os mesmos dados e envie:
- matriz curricular;
- perfil do egresso;
- ementário.

## Resultado

O sistema apresenta:
- Plano de Ensino;
- Diagnóstico curricular;
- Rastreabilidade dos 16 capítulos;
- Auditoria;
- JSON estruturado para futura integração com o AVA.

