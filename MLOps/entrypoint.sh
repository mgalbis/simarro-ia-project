# Script de inicialización del contenedor JupyterHub.
# Se ejecuta cada vez que arranca el contenedor y añadimos los usuarios y dependencias.

echo "Instalando dependencias Python..."
/srv/venv/bin/pip install --quiet jupyterlab mlflow lakefs-sdk scikit-learn pandas numpy xgboost evidently

echo "Creando usuarios del proyecto..."
for user in casoA casoB casoC casoD casoE casoF casoG casoH casoI casoJ casoK admin; do
    useradd -m -s /bin/bash $user 2>/dev/null || echo "Usuario $user ya existe"
    echo "$user:simarro2026" | chpasswd
done

echo "Arrancando JupyterHub..."
jupyterhub