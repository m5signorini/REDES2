# Practica2
Practica 2 de Redes II: **Secure Box**
Realizado por Ana Calzada y Martín Sánchez.
## Instalación
Para esta prática se ha utilizado Python 3.6.9. Además se hace uso de varias librerías especificadas en el fichero _requirements.txt_.
La práctica consta de un script ejecutable para pequeños tests del módulo de cifrado, y del ejecutable principal de la aplicación _secure\_box_. Así pues, para poder usar la aplicación se puede utilizar el comando _make init_ para instalar los paquetes requeridos. En caso de fallo, quedan especificados aun así qué paquetes son necesarios en el fichero _requirements.txt_.

## Ejecución
Para ejecutar la práctica se puede utilizar el Makefile usando la opción _run_ lo cual mostrará la ayuda de todos los posibles comandos, aun así en general se puede usar el siguiente comando dentro del directorio _secure-box_:
```sh
python3 securebox_client.py
```
**Importante**: Nótese que para poder utilizar plenamente la aplicación se pide al usuario que introduzca su token para poder utilizar la API y comunicarse así con el servidor. El token puede introduirse tanto manualmente la primera vez que se solicita en la terminal o rellenando el fichero _user-data/token.txt_. Hará falta actualizar manualmente el token cada vez que este caduque o sea eliminado al borrar el usuario del servidor, en cualquier caso se notificará un error si el token no es válido y se intenta acceder al servidor.
## Documentación
La documentación precisa de la práctica se encuentra en la sección de la wiki, además de en los comentarios en el código.
