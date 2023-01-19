import subprocess
import re
import sys


def run_mypy(project_path):
    # Run mypy on the project
    mypy_output = subprocess.run(['poetry', 'run', 'mypy', project_path], capture_output=True)
    mypy_output = mypy_output.stdout.decode()
    # mypy_output = 'inapps/api/message.py:410: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]\ninapps/api/message.py:416: error: Call to untyped function "product_line_permission_required" in typed context  [no-untyped-call]\ninapps/api/message.py:417: error: Function is missing a type annotation  [no-untyped-def]\ninapps/api/message.py:418: error: Call to untyped function "get_filter" in typed context  [no-untyped-call]\ninapps/views/__init__.py:9: error: Module "inapps.views.lists" does not explicitly export attribute "get_pagination"  [attr-defined]\nFound 1344 errors in 110 files (checked 267 source files)\n'

    # Parse mypy output for errors
    error_lines = {}
    for line in mypy_output.split('\n'):
        if ': error:' in line:
            file_name, line_number, error_message = re.match(r'(.*):(\d+): error: (.*)', line).groups()

            if error_message.startswith("Unused") and error_message.endswith("comment"): # Unused "..." comment
                continue

            error_code = error_message.split(' ')[-1]
            if not (error_code[0] == '[' and error_code[-1] == ']'):
                breakpoint()

            error_code = error_code[1:-1]
            if file_name not in error_lines:
                error_lines[file_name] = {}

            if line_number not in error_lines[file_name]:
                error_lines[file_name][line_number] = []

            error_lines[file_name][line_number].append(error_code)

    # Add # mypy: ignore to each line with an error
    for file in error_lines.keys():
        with open(file, 'r') as f:
            lines = f.readlines()
        for line_number, error_codes in error_lines[file].items():
            line_to_alter = lines[int(line_number) - 1].rstrip()

            if 'type: ignore' in line_to_alter:
                # Remove type: ignore from line, we'll run mypy once again in a moment.
                line_to_alter = line_to_alter.split('# type: ignore')[0]
                lines[int(line_number) - 1] = f"{line_to_alter}\n"
                continue

            all_error_codes = ','.join(error_codes)
            lines[int(line_number) - 1] = f"{line_to_alter} # type: ignore[{all_error_codes}]\n"

        # Overwrite the file with the updated lines
        with open(file, 'w') as f:
            f.writelines(lines)


def run_black(project_path):
    black_output = subprocess.run(['poetry', 'run', 'black', project_path], capture_output=True)
    black_output = black_output.stdout.decode()


def run_mypy_cleanup(project_path):
    mypy_output = subprocess.run(['poetry', 'run', 'mypy', project_path], capture_output=True)
    mypy_output = mypy_output.stdout.decode()

    unused_error_lines = {}
    for line in mypy_output.split('\n'):
        if ': error:' in line:
            file_name, line_number, error_message = re.match(r'(.*):(\d+): error: (.*)', line).groups()

            if not(error_message.startswith("Unused") and error_message.endswith("comment")): # Unused "..." comment
                breakpoint()

            if file_name not in unused_error_lines:
                unused_error_lines[file_name] = []

            unused_error_lines[file_name].append(line_number)


    # Add # mypy: ignore to each line with an error
    for file in unused_error_lines.keys():
        with open(file, 'r') as f:
            lines = f.readlines()
        for line_number in unused_error_lines[file]:
            line_to_alter = lines[int(line_number) - 1].rstrip()

            if 'type: ignore' in line_to_alter:
                # Remove type: ignore from line, we'll run mypy once again in a moment.
                line_to_alter = line_to_alter.split('# type: ignore', 2)[0]
                lines[int(line_number) - 1] = f"{line_to_alter}\n"
                continue

        # Overwrite the file with the updated lines
        with open(file, 'w') as f:
            f.writelines(lines)


if __name__ == '__main__':
    path = sys.argv[1]
    print(f"""
    running mypy on {path=} for the first time. It will remove existing type: ignore so they can be later merged in second step.
    """)
    run_mypy(path)

    print(f"""
    running mypy on {path=} for the second time. It will add ignore to errors removed in previous step merged with new ones.
    """)
    run_mypy(path)

    print(f"""
    running black on {path=}. Optional - it only formats
    """)
    run_black(path)

    print(f"""
    running mypy on {path=} for the third time. It will add ignore for errors ignored by black.
    """)
    run_mypy(path)

    print(f"""
    running mypy cleanup on {path=}". It will remove ignores that are no onger applicable.
    """)
    run_mypy_cleanup(path)
