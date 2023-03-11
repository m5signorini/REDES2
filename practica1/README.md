# Practica1
Practica 1 de Redes II: Servidor Web
Realizado por Ana Calzada y Martín Sánchez.
## Instalación
Para la ejecución de la práctica hace falta tener instalada la librería _confuse_, el resto de los ficheros necesarios se encuentra en este repositorio, salvo los archivos para la página web. Una vez descargado este repositorio se puede compilar utilizando _make_.

## Ejecución
La práctica cuenta con varios ejecutables, los cuales se han usado para diversas pruebas y tests.
Así pues el único ejecutable final es _fork\_pool\_server_ el cual se puede ejecutar por ejemplo de la siguiente manera:
```sh
./fork_pool_server 10
```
Donde el número hace referencia al número de procesos hijos a crear.
Nótese que para poder ejecutar convenientemente el servidor hace falta rellenar el fichero de configuración, el cual cuenta con opciones como el nombre del servidor, el puerto a usar, el directorio donde se encuentran los recursos web así como (opcionalmente) se pueden especificar dentro de los recursos web documentos html para usar en caso de error.
## Documentación
La documentación precisa de la práctica se encuentra en la sección de la wiki, además de en los comentarios en el código en sí.
