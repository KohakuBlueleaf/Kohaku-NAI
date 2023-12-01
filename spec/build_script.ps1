.\venv\Scripts\activate

# Compile all the scripts
pyinstaller -y .\spec\pyi_build_internals.spec
pyinstaller -y .\spec\gen_server.spec
pyinstaller -y .\spec\gr_client.spec
pyinstaller -y .\spec\runner.spec
pyinstaller -y .\spec\dc_bots_main.spec


# Copy files into bundle
New-Item -ItemType Directory -Force -Path .\dist\KohakuNAI-bundle
Copy-Item -Force -Recurse .\dist\pyi_build_internals\_internal .\dist\KohakuNAI-bundle
Copy-Item -Force .\dist\gen_server\gen_server.exe .\dist\KohakuNAI-bundle\
Copy-Item -Force .\dist\gr_client\gr_client.exe .\dist\KohakuNAI-bundle\
Copy-Item -Force .\dist\runner\runner.exe .\dist\KohakuNAI-bundle\
Copy-Item -Force .\dist\dc_bots_main\dc_bots_main.exe .\dist\KohakuNAI-bundle\

Copy-Item -Force -Recurse .\client_extensions .\dist\KohakuNAI-bundle
Copy-Item -Force .\config.toml .\dist\KohakuNAI-bundle
Copy-Item -Force .\dc-bot-config.json .\dist\KohakuNAI-bundle
Copy-Item -Force .\client.css .\dist\KohakuNAI-bundle


# Remove redundent files
Remove-Item -Recurse .\dist\KohakuNAI-bundle\_internal\gradio\node\dev
Remove-Item -Recurse -Include *.map .\dist\KohakuNAI-bundle\_internal\gradio