# JARVIS App

App de chat pessoal (Android) para o núcleo JARVIS, usando a API da Groq.

## O que tem aqui

- `main.py` — a interface (tela de chat + tela de configuração da chave)
- `config.py` — salva a chave da API localmente no aparelho (nunca no código)
- `jarvis_core_v2_groq.py` — o núcleo que você já tinha (memória, contexto, conector Groq)
- `buildozer.spec` — receita de como empacotar isso num `.apk`
- `.github/workflows/build.yml` — compila o APK automaticamente na nuvem

## Por que não gerar o APK num site genérico

Esses sites de "Python para APK" costumam travar porque compilar para Android
exige baixar o Android SDK + NDK (vários GB) e compilar o Python inteiro para
ARM — isso é pesado e demorado, e servidores compartilhados grátis costumam
não aguentar ou dar timeout depois de horas. É provavelmente por isso que
você ficou 6h esperando e no fim deu erro.

O jeito confiável e gratuito é deixar o **GitHub Actions** fazer esse trabalho
pesado pra você (ele já vem com tudo pronto e cacheado). Veja como:

## Passo a passo para gerar o APK

1. Crie uma conta no GitHub (se ainda não tiver) e crie um repositório novo
   (pode ser privado).
2. Suba todos os arquivos desta pasta para esse repositório, mantendo a
   mesma estrutura (incluindo a pasta `.github/workflows/`).
3. No repositório, vá na aba **Actions**.
4. Clique no workflow "Build JARVIS APK" e depois em **Run workflow**.
5. Espere terminar (a primeira vez demora uns 15–25 minutos; as próximas são
   mais rápidas). Acompanhe o log — se der erro, ele aparece ali, texto por
   texto, bem mais fácil de resolver do que um site travando sem explicação.
6. Quando terminar, abra a execução concluída e baixe o artefato
   **jarvis-apk** (é um `.zip` com o `.apk` dentro).
7. Transfira o `.apk` pro seu celular e instale (o Android vai pedir pra
   permitir "instalar de fontes desconhecidas" — normal para apps fora da
   Play Store).

## Ao abrir o app pela primeira vez

Ele vai pedir sua chave da API da Groq (gerada em console.groq.com → API
Keys). Cole a chave, salve, e a tela de chat abre. A chave fica guardada só
naquele aparelho, dentro da pasta de dados do próprio app.

## Se algo der errado no build

Me mande a mensagem de erro exata do log do GitHub Actions — com ela eu
consigo te dizer exatamente o que ajustar (é bem mais fácil de diagnosticar
do que um site de terceiros sem log nenhum).
