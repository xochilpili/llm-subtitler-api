# LLM Subtitler using Whisper

Api Service that translates srt files and transcript large wav audios.
**Warning** This service it's intended to use with **CUDA**.

##### Configure python & Run locally

-   Install python
    ```sh
        curl https://pyenv.run | bash
        # Add pyenv to PATH
        export PATH="$HOME/.pyenv/bin:$PATH"
        eval "$(pyenv init --path)"
        eval "$(pyenv init -)"
        eval "$(pyenv virtualenv-init -)"
        source ~/.bashrc
    ```
-   Install python 3.9.9
    ```sh
        # install python v3.9.9
        pyenv install 3.9.9
        # set globally python v3.9.9
        pyenv global 3.9.9
    ```
-   Activate Virtualenv
    ```sh
        # create a python's 3.9.9 virtual environment called 'pycuda'
        pyenv virtualenv 3.9.9 pycuda
        # Activate virtual env
        pyenv activate pycuda
    ```
-   Install dependencies
    ```sh
        # LLM Models and torch can be take a while to download...
        pip install -r requirements.txt
    ```
-   Add env file
    ```sh
        LLM_HOST=0.0.0.0
        LLM_PORT=4003
        LLM_NOTIFICATION_SERVICE_URL=your-http-service
    ```
-   Run locally
    ```sh
        python main.py
    ```

#### To run with docker

First validate that you've installed **nvidia-container-toolkit** in your host.

```sh
    # build image
    docker build -t llm-subtitler:main -f Dockerfile .
    # run built image as container
    docker run --rm -p 4003:4003 llm-subtitler:main
```

#### How to install nvidia-container-toolkit in F40

```sh
    # download & save nvidia's repository
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo \
    | tee /etc/yum.repos.d/nvidia-container-toolkit.repo
    # install nvidia container
    dnf -y install nvidia-container-toolkit --refresh
    # enable nvidia runtime to docker
    nvidia-ctk runtime configure --runtime=docker
    # restart docker service
    systemctl restart docker
```

#### Usage

##### Translate SRT files

When translate an _srt_ file from any language to another language, we need to specify a file and a desired language as output language. Once finish translation, then will send a request notifying that task has been completed to any HTTP service you define in `LLM_NOTIFICATION_SERVICE_URL` environment variable.

```sh
# Send a local srt file to be translated and pass desired language to translate to.
curl -X POST 'http://localhost:4003/translate' -F 'file=@/path/subtitle.srt' -F 'lang=es'
```

##### Transcript Audio

As a requirement we need to send via http an audio file with the following pre-requisites:

-   Should be a wav file
-   Should be at 16Hz
-   Audio codec should be pcm_s16le
-   Should be MONO (1 channel)
    To extract audio from a video with these characteristics please use:

```sh
ffmpeg -i video/path/video.mp4 -ac 1 -ar 16000 -c:a pcm_s16le output.wav
```

ffmpeg will extract audio from a video with those specs.
Then, we can use **llm-subtitler-api** service to transcribe.

```sh
curl -X POST 'http://localhost:4003/transcribe' -F 'file=@/path/output.wav' -F 'lang=es'
```

Because **llm-subtitler-api** is using VAD, then will detect automatically source audio language, so request's param `lang` will automatically translate the transcription from Whisper. In this example, output subtitles will be in spanish.

##### Get output (Translation/Transcript subtitles)

```sh
curl 'http://localhost:4003/download?filename=filename_from_completed_task'
```

#### Maintainers

xOCh <xochilpili@gmail.com>

### License

MIT
