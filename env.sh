PYTHON=desres-python/2.7.14-02c7
PYTHON3=desres-python/3.6.2-02c7
YAS=yas/0.73-beta-c7

garden prepend-path PYTHONPATH $(dirname $0)/../lib/python
garden load $PYTHON/bin
garden load $YAS/lib-python
