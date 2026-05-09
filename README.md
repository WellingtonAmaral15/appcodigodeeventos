# appcodigodeeventos
Projeto de análise de falhas, através da interpretação de códigos gerados pelos equipamentos ferroviários

## Preparacao para Android/iOS

Este projeto usa Kivy. Para Android, o caminho recomendado e gerar o APK/AAB com Buildozer em Linux, macOS ou WSL no Windows.

Arquivos adicionados/ajustados:

- `requirements.txt`: dependencias do app.
- `buildozer.spec`: configuracao inicial para gerar APK Android.
- `main.py`: leitura dos `.xlsm` feita com `openpyxl`, evitando `pandas` no mobile.

### Testar no computador

```powershell
python -m pip install -r requirements.txt
python main.py
```

### Gerar APK no WSL/Linux

```bash
pip install buildozer
buildozer android debug
```

O APK de debug sera gerado na pasta `bin/`.

### iOS

Para iOS, o empacotamento Kivy exige macOS/Xcode. O mesmo codigo Kivy pode ser reaproveitado, mas o build precisa ser feito em ambiente Apple.

## Publicacao web 24h

Para deixar o sistema disponivel pela internet, mesmo com o computador desligado, publique a versao web em uma hospedagem na nuvem.

Arquivos ja preparados para isso:

- `web_app.py`: servidor web do sistema.
- `requirements-web.txt`: dependencias da versao web.
- `Dockerfile`: empacotamento para Render, Railway e plataformas compativeis com Docker.

### Opcao simples com Render ou Railway

1. Envie este projeto para um repositorio no GitHub.
2. Crie um novo servico web na plataforma escolhida.
3. Aponte o deploy para este repositorio.
4. Se a plataforma pedir comando manual:

```bash
pip install -r requirements-web.txt
python web_app.py --host 0.0.0.0
```

5. Se preferir, use o `Dockerfile` do projeto e a plataforma fara o build automaticamente.

O app le a porta pela variavel `PORT`, entao ele funciona em hospedagens que definem a porta automaticamente.

### Dominio proprio

Depois do deploy, voce pode:

- usar o dominio publico da plataforma
- conectar um dominio proprio
- ativar HTTPS automatico oferecido pela hospedagem

