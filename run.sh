if [ "$1" = "--setup" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    venv/bin/pip3 install -r requirements.txt
    # if .env doest exist copy over .env.example
    if [ ! -f ".env" ]; then
        echo "Copying .env.example to .env..."
        cp .env.example .env
    fi
    echo "Done!"
fi
venv/bin/python3 main.py