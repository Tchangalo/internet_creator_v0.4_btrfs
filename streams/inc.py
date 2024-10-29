from flask import Flask, render_template, request, redirect, url_for, flash
import subprocess
import os
import sys
import select

app = Flask(__name__)
app.secret_key = 'my_secret_key'  # Hier einen sicheren Schlüssel verwenden

# Skriptverzeichnisse
GENERAL_SCRIPT_DIR = "/home/user/streams/ks/"
OTHER_SCRIPT_DIR = "/home/user/streams/"
IMAGE_PATH = "/static/mplan.png"

def ensure_config_dir_exists():
    if not os.path.exists(GENERAL_SCRIPT_DIR):
        os.makedirs(GENERAL_SCRIPT_DIR)


def call_script(script_dir, script_name, *args):
    command = f"bash {script_dir}{script_name} {' '.join(map(str, args))}"
    print(f"Executing command: {command}")  # Debug-Ausgabe

    env = os.environ.copy()
    env["ANSIBLE_FORCE_COLOR"] = "true"

    # Liste von Keywords, die in den zu ignorierenden Warnungen vorkommen
    ignore_keywords = ["interpreter", "ansible", "python", "idempotency", "configuration", "device"]

    try:
        with subprocess.Popen(command, shell=True, executable="/bin/bash",
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, env=env, bufsize=1) as process:

            while True:
                reads = [process.stdout.fileno(), process.stderr.fileno()]
                ret = select.select(reads, [], [])

                # Echtzeitausgabe von stdout (Download-Status)
                if process.stdout.fileno() in ret[0]:
                    line = process.stdout.readline()
                    if line:
                        print(line, end='', flush=True)  # Echtzeitausgabe für stdout

                # Filtern und Ausblenden von Warnungen basierend auf Keywords
                if process.stderr.fileno() in ret[0]:
                    line = process.stderr.readline()
                    if line:
                        # Ignorieren, wenn eine der Ignore-Keywords in der Zeile vorkommt
                        if not any(keyword in line.lower() for keyword in ignore_keywords):
                            print(line, end='', flush=True)  # Andere Fehler sofort anzeigen

                # Beenden, wenn der Prozess abgeschlossen ist
                if process.poll() is not None:
                    break

            # Warten, bis der Prozess vollständig abgeschlossen ist
            process.wait()

            # Erfolg oder Fehler melden
            if process.returncode == 0:
                flash(f"Script {script_name} executed successfully!", "success")
            else:
                flash(f"Script {script_name} failed with exit code {process.returncode}.", "error")

    except FileNotFoundError:
        flash(f"Script {script_name} not found or invalid command!", "error")
        print(f"Script {script_name} not found or invalid command!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/provider', methods=['GET', 'POST'])
def provider():
    if request.method == 'POST':
        args = [request.form.get(label, "") for label in ["Node", "Provider", "Routers", "Limit", "Start Delay"]]
        args.insert(2, "1")  # Fügt Destroy als Argument hinzu

        # Überprüfen, ob die Checkbox "Refresh Vyos Upgrade Version" aktiviert ist
        refresh_vyos_upgrade_version = "1" if request.form.get("refresh_vyos_upgrade") else "0"
        args.append(refresh_vyos_upgrade_version)  # Positionale Variable hinzufügen
        
        script_name = "provider_serial.sh" if request.form.get("Serial Mode") else "provider.sh"
        call_script(OTHER_SCRIPT_DIR, script_name, *args)

        return redirect(url_for('provider'))

    return render_template('provider.html')

@app.route('/provider-turbo', methods=['GET', 'POST'])
def provider_turbo():
    if request.method == 'POST':
        args = [request.form.get(label, "") for label in ["Node", "Provider", "Routers", "Limit"]]
        args.insert(2, "1")  # Fügt Destroy als Argument hinzu

        # Überprüfen, ob die Checkbox "Refresh Vyos Upgrade Version" aktiviert ist
        refresh_vyos_upgrade_version = "1" if request.form.get("refresh_vyos_upgrade") else "0"
        args.append(refresh_vyos_upgrade_version)  # Positionale Variable hinzufügen
        
        call_script(OTHER_SCRIPT_DIR, "provider_turbo.sh", *args)
        return redirect(url_for('provider_turbo'))

    return render_template('provider_turbo.html')

@app.route('/single-router', methods=['GET', 'POST'])
def single_router():
    if request.method == 'POST':
        args = [
            request.form.get("Node", ""),
            request.form.get("Provider", ""),
            "1",  # Fügt Destroy als Argument hinzu
            request.form.get("Router", "")
        ]
        
        # Überprüfen, ob die Checkbox "Refresh Vyos Upgrade Version" aktiviert ist
        refresh_vyos_upgrade_version = "1" if request.form.get("refresh_vyos_upgrade") else "0"
        args.append(refresh_vyos_upgrade_version)  # Fünfte positionale Variable hinzufügen
        
        call_script(OTHER_SCRIPT_DIR, "single_router.sh", *args)
        return redirect(url_for('single_router'))

    return render_template('single_router.html')

@app.route('/general', methods=['GET', 'POST'])
def general():
    if request.method == 'POST':
        # Unterscheiden, welcher Button gesendet wurde und das entsprechende Skript aufrufen
        if 'restart_isp1' in request.form:
            isp1_routers = request.form.get("restart_isp1_routers", "")
            isp1_delay = request.form.get("restart_isp1_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "restart_isp1.sh", isp1_routers, isp1_delay)
        elif 'restart_isp2' in request.form:
            isp2_routers = request.form.get("restart_isp2_routers", "")
            isp2_delay = request.form.get("restart_isp2_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "restart_isp2.sh", isp2_routers, isp2_delay)
        elif 'restart_isp3' in request.form:
            isp3_routers = request.form.get("restart_isp3_routers", "")
            isp3_delay = request.form.get("restart_isp3_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "restart_isp3.sh", isp3_routers, isp3_delay)

        elif 'start_isp1' in request.form:
            start_isp1_routers = request.form.get("start_isp1_routers", "")
            start_isp1_delay = request.form.get("start_isp1_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "start_isp1.sh", start_isp1_routers, start_isp1_delay)
        elif 'start_isp2' in request.form:
            start_isp2_routers = request.form.get("start_isp2_routers", "")
            start_isp2_delay = request.form.get("start_isp2_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "start_isp2.sh", start_isp2_routers, start_isp2_delay)
        elif 'start_isp3' in request.form:
            start_isp3_routers = request.form.get("start_isp3_routers", "")
            start_isp3_delay = request.form.get("start_isp3_delay", "")
            call_script(GENERAL_SCRIPT_DIR, "start_isp3.sh", start_isp3_routers, start_isp3_delay)

        elif 'shutdown_isp1' in request.form:
            shutdown_isp1 = request.form.get("shutdown_isp1", "")
            call_script(GENERAL_SCRIPT_DIR, "shutdown_isp1.sh", shutdown_isp1)
        elif 'shutdown_isp2' in request.form:
            shutdown_isp2 = request.form.get("shutdown_isp2", "")
            call_script(GENERAL_SCRIPT_DIR, "shutdown_isp2.sh", shutdown_isp2)
        elif 'shutdown_isp3' in request.form:
            shutdown_isp3 = request.form.get("shutdown_isp3", "")
            call_script(GENERAL_SCRIPT_DIR, "shutdown_isp3.sh", shutdown_isp3)

        elif 'destroy_isp1' in request.form:
            destroy_isp1 = request.form.get("destroy_isp1", "")
            call_script(GENERAL_SCRIPT_DIR, "destroy_isp1.sh", destroy_isp1)
        elif 'destroy_isp2' in request.form:
            destroy_isp2 = request.form.get("destroy_isp2", "")
            call_script(GENERAL_SCRIPT_DIR, "destroy_isp2.sh", destroy_isp2)
        elif 'destroy_isp3' in request.form:
            destroy_isp3 = request.form.get("destroy_isp3", "")
            call_script(GENERAL_SCRIPT_DIR, "destroy_isp3.sh", destroy_isp3)

        return redirect(url_for('general'))

    return render_template('general.html')

if __name__ == '__main__':
    ensure_config_dir_exists()
    app.run(debug=True, host='0.0.0.0')
