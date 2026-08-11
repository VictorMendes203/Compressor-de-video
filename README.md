# compress.vid

Compressor de vídeo que roda **inteiramente no navegador**, usando FFmpeg.wasm.
Nenhum vídeo é enviado a servidor algum — tudo acontece no dispositivo da pessoa.

## Rodando localmente

Não precisa de build nem instalação. É um único arquivo HTML.

```bash
# qualquer servidor estático funciona, por exemplo:
npx serve .
```

Depois abra o endereço que aparecer (geralmente `http://localhost:3000`).

> Não abra o `index.html` clicando duas vezes (`file://`) — o navegador bloqueia
> os módulos JavaScript por segurança. Precisa ser servido via `http://`.

## Deploy no Vercel

Esse projeto é um site **estático** (HTML puro), então não precisa de nenhuma
configuração especial — nada de Python, Node build, etc.

1. Suba esta pasta para um repositório no GitHub
2. No [vercel.com](https://vercel.com), clique em "Add New → Project"
3. Selecione o repositório
4. Em "Framework Preset", deixe como **Other** (ou "Static")
5. Não precisa configurar Build Command nem Output Directory
6. Clique em Deploy

Pronto — em menos de um minuto o site estará no ar.

## Como funciona

- [`@ffmpeg/ffmpeg`](https://github.com/ffmpegwasm/ffmpeg.wasm) compila o FFmpeg
  para WebAssembly, permitindo rodar no navegador
- O vídeo é carregado na memória do navegador, processado localmente, e o
  resultado é oferecido como download — sem upload em nenhum momento
- Funciona offline depois do primeiro carregamento (os arquivos do FFmpeg.wasm
  ficam em cache do navegador)

## Limitações

- Arquivos muito grandes (1GB+) podem ser lentos ou travar em dispositivos
  com pouca memória, já que tudo roda no navegador
- Velocidade de compressão é menor que a de um FFmpeg nativo instalado
