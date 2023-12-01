import launch


additional_requirements = ["toml", "curl_cffi", "httpx"]


for req in additional_requirements:
    if not launch.is_installed(req):
        launch.run_pip(f"install {req}", "requirements for Kohaku-NAI")
