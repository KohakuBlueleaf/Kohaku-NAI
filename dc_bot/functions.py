def make_summary(generate_config, prefix):
    summary = f'{prefix}novelai '
    summary += (
        f'"{generate_config["prompt"]}" '
        f'"{generate_config["negative_prompt"]}" '
        f'{("-QU " if generate_config["quality_tags"] else "")}'
        f'-UC {generate_config["ucpreset"]} '
        f'-W {generate_config["width"]} '
        f'-H {generate_config["height"]} '
        f'--steps {generate_config["steps"]} '
        f'--scale {generate_config["scale"]} '
        f'-S {generate_config["seed"]} '
        f'--sampler {generate_config["sampler"]} '
        f'--schedule {generate_config["schedule"]} '
    )
    return f'```\n{summary}\n```'


'''
Error logging
'''
def log_error_command(err):
    errors = err.split('\n\n')[0].strip().split('\n')
    if errors[1][-10:]=='in wrapped':
        line = 3
    else:
        line = 1

    err_file, err_line, err_pos = errors[line].strip().split(', ')
    err_program = errors[line+1].strip()
    err_cls, err_mes = errors[-1].split(': ',1)
    print(
        '====Error Occured====\n',
        'Error File   : {}\n'.format(err_file.split()[-1]),
        'Error Line   : {}\n'.format(err_line.split()[-1]),
        'Error Pos    : {}\n'.format(err_pos.split()[-1]),
        'Error program: {}\n'.format(err_program),
        'Error Class  : {}\n'.format(err_cls),
        'Error Message: {}\n'.format(err_mes),
        '=====================',
        sep=''
    )


def log_error_event(err):
    errors = err.split('\n\n')[0].strip().split('\n')

    err_file, err_line, err_pos = errors[-3].strip().split(', ')
    err_program = errors[-2].strip()
    err_cls, err_mes = errors[-1].split(': ',1)
    print(
        '====Error Occured====\n',
        'Error File   : {}\n'.format(err_file.split()[-1]),
        'Error Line   : {}\n'.format(err_line.split()[-1]),
        'Error Pos    : {}\n'.format(err_pos.split()[-1]),
        'Error program: {}\n'.format(err_program),
        'Error Class  : {}\n'.format(err_cls),
        'Error Message: {}\n'.format(err_mes),
        '=====================',
        sep=''
    )