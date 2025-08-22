#!/bin/bash
success=0
error=1
verbose=0 # 0 false, 1 true

function ifverbose () 
{
    if [ $verbose == 1 ] ; then
        echo $@
    fi
}
#lo siguiente esta preparado para poner un for, e iterar por los parametros, utilizando el case para identificarlos
if [ $# -ge 1 ] ; then
    case $1 in
        --v)
            let verbose=1
        ;;
    esac
fi

cd $(dirname $0)


if [ ! -f local/Company.data ]; then  
	cp local/Company.data.example local/Company.data 2> /dev/null
        if [ $? != $success ] ; then
            ifverbose "No se pudo copiar el archivo settings/settings.xml.example a settings/settings.xml"
            ifverbose "Retornando con error"
            exit $error
        fi
fi
if [ ! -f local/LocalSettings.data ]; then 
	cp local/LocalSettings.data.example local/LocalSettings.data 2> /dev/null
        if [ $? != $success ] ; then
            ifverbose "No se pudo copiar el archivo settings/settings.xml.example a settings/settings.xml"
            ifverbose "Retornando con error"
            exit $error
        fi
fi
if [ ! -f local/DocumentPrinter.data ]; then 
	cp local/DocumentPrinter.data.example local/DocumentPrinter.data 2> /dev/null
        if [ $? != $success ] ; then
            ifverbose "No se pudo copiar el archivo settings/settings.xml.example a settings/settings.xml"
            ifverbose "Retornando con error"
            exit $error
        fi
fi

# crea enlaces necesarios:
cd lib
ln -s libcrypto.so.0.9.8        libcrypto.so.0.9.7      2> /dev/null
ln -s libcrypto.so.0.9.8        libcrypto.so.0          2> /dev/null
ln -s libssl.so.0.9.8           libssl.so.0.9.7         2> /dev/null
ln -s libssl.so.0.9.8           libssl.so.0             2> /dev/null
ln -s libmysqlclient.so.14.0.0  libmysqlclient.so.14    2> /dev/null
# el siguiente es un poco extraño, tal vez la cosa debería ser al revez.
ln -s libpython2.4.so       libpython2.4.so.1.0         2> /dev/null 
cd ..

ifverbose "La inicializacion termino con exito..."
exit $success 
