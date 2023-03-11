
## Tipo de servidor

El primer paso de la práctica es elegir el tipo de servidor a implementar de entre los vistos en teoría. Para ello, implementamos un cliente de prueba, que envíe peticiones simples (un mensaje de saludo), de forma que el servidor tenga que leerlas y contestar con un mensaje de despedida. Una vez hecho esto, implementamos tres tipos de servidores para probar su funcionamiento. A saber, los que siguen:
* Servidor iterativo: Este tipo de servidor tiene un único proceso principal que atiende las peticiones del cliente de una en una en un bucle continuo hasta llegar al máximo de conexiones permitidas.
* Servidor concurrente: Este tipo de servidor crea un proceso hijo por cada nueva petición recibida, el cual la atiende y termina. El proceso padre sigue creando hijos mientras sigan llegando peticiones, hasta alcanzar el máximo.
* Pool de hijos: En este tipo de servidor, el proceso padre crea tantos hijos como se le hayan pasado por parámetro, y cada uno de estos va aceptando y procesando conexiones mientras lleguen, hasta alcanzar el máximo. Para facilitar la creación de este tipo de servidor, se creó el módulo child, que contiene las acciones principales a realizar por el proceso hijo.

Para elegir cuál de estos servidores usar, medimos el tiempo que tardan en responder a un número dado de peticiones y comprobamos cuál es el más rápido. Para 5000 conexiones, los tiempos obtenidos son estos:
* Servidor iterativo ->    real: 0m0,133s,	user: 0m0,360s,	sys: 0m0,120s
* Servidor concurrente ->  real: 0m0,277s,	user: 0m0,350s,	sys: 0m0,100s
* Pool de hijos -> 	    real: 0m0,116s,	user: 0m0,365s,	sys: 0m0,125s

## Verbos GET, POST, HEAD y OPTIONS

La implementación de las funcionalidades correspondiente a estos verbos se realiza en en el módulo http. La función principal, http\_process_request, procesa la petición recibida y llama a la función correspondiente según si la petición se corresponde con un GET, HEAD, POST u OPTIONS. 
* Si es un GET, se buscará el recurso pedido para devolverlo si existe junto con un código de éxito, o se informará de un error con el código correspondiente.
* Si es un POST, se abrirá el archivo correspondiente al path dado en modo escritura y se añadirá al mismo los datos que se hayan pasado. Devolverá las cabeceras correspondientes o un código de error en caso de que haya un problema.
* Si es un HEAD, se devolverán las cabeceras del recurso pedido o el código de error correspondiente en caso de que haya un problema.
* Si es un OPTIONS, se devolverán los métodos que se pueden usar (HEAD, GET, POST).

En cuanto a los códigos de error, el servidor puede devolver los siguientes:
* 100 Continue
* 200 OK
* 400 Bad Request
* 404 Not Found
* 413 Payload Too Large
* 415 Unsupported Media Type
* 500 Server Error
* 501 Not Implemented

En el caso de los errores 400 y 404, el servidor devuelve también un documento html que informa al usuario del error de una forma más visual, ya que consideramos que estos dos errores son los que ocurrirán con más frecuencia y por tanto los más relevantes.

## Configuración del servidor

El servidor se configura con los datos contenidos en server.conf, los cuales parsea haciendo uso de la librería libconfuse. En el fichero de configuración se encuentran los siguientes elementos:
* server_root, que contiene el directorio raíz desde donde el servidor debe buscar los recursos pedidos. Se concatenará al path relativo de un recurso para construir la ruta final.
* max_clients, que indica el número máximo de conexiones que el servidor aceptará.
* listen_port, que indica el puerto de escucha del servidor, por donde recibirá las conexiones y las peticiones.
* server_signature, que indica el nombre público del servidor. Dicho nombre se mostrará cuando el servidor esté listo para recibir en un mensaje que informa al cliente de esto mismo.
* doc\_code\_400 y doc\_code_404, que contienen el path hasta los archivos html correspondientes a los errores 400 y 404, respectivamente. Estos se mostrarán cuando corresponda para informar al usuario de una forma más visual del error cometido.

## Ejecución de scripts

El módulo encargado de la ejecución de scripts en python y php es cgi. Para ello, recibida una petición GET o POST, se comprueba si el recurso pedido es un script mirando su extensión. En el caso de que lo sea, se procede a ejecutarlos.

