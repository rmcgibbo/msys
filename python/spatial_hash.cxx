#define NO_IMPORT_ARRAY 1
#include "unique_symbol.hxx"
#include "spatial_hash.hxx"
#include "wrap_obj.hxx"

using namespace boost::python;
using namespace desres::msys;

static SpatialHash* hash_new(PyObject* posobj, PyObject* idobj, PyObject* boxobj) {

    PyObject* posarr = PyArray_FromAny(posobj,
                PyArray_DescrFromType(NPY_FLOAT32),
                2, 2, NPY_C_CONTIGUOUS | NPY_ALIGNED,
                NULL);
    if (!posarr) throw_error_already_set();

    PyObject* idarr = PyArray_FromAny(idobj,
                PyArray_DescrFromType(NPY_UINT32),
                1, 1, NPY_C_CONTIGUOUS | NPY_ALIGNED,
                NULL);
    if (!idarr) {
        Py_DECREF(posarr);
        throw_error_already_set();
    }

    PyObject* boxarr = NULL;
    if (boxobj!=Py_None) {
        boxarr = PyArray_FromAny(boxobj,
                 PyArray_DescrFromType(NPY_FLOAT64),
                 2, 2, NPY_C_CONTIGUOUS | NPY_ALIGNED,
                 NULL);
        if (!boxarr) {
            Py_DECREF(idarr);
            Py_DECREF(posarr);
            throw_error_already_set();
        }
    }

    const float* pos = (const float*)PyArray_DATA(posarr);
    const Id* ids = (const Id*)PyArray_DATA(idarr);
    const double* box = boxarr ? (const double *)PyArray_DATA(boxarr) : NULL;
    Id n = PyArray_DIM(idarr,0);

    auto hash = new SpatialHash(pos, n, ids, box);

    Py_XDECREF(boxarr);
    Py_DECREF(idarr);
    Py_DECREF(posarr);
    return hash;
}


template <typename Func, typename Param>
static PyObject* hash_find(SpatialHash& hash,
                           Param r,
                           PyObject* posobj,
                           PyObject* idsobj,
                           Func func) {

    PyObject* posarr = PyArray_FromAny(posobj,
                PyArray_DescrFromType(NPY_FLOAT32),
                2, 2, NPY_C_CONTIGUOUS | NPY_ALIGNED,
                NULL);
    if (!posarr) throw_error_already_set();

    PyObject* idsarr = PyArray_FromAny(idsobj,
                PyArray_DescrFromType(NPY_UINT32),
                1, 1, NPY_C_CONTIGUOUS | NPY_ALIGNED,
                NULL);
    if (!idsarr) {
        Py_DECREF(posarr);
        throw_error_already_set();
    }

    const float* pos = (const float*)PyArray_DATA(posarr);
    const Id* ids = (const Id*)PyArray_DATA(idsarr);
    Id n = PyArray_DIM(idsarr,0);
    for (Id i=0; i<n; i++) {
        if (ids[i]>=PyArray_DIM(posarr,0)) {
            PyErr_Format(PyExc_ValueError, "index out of bounds: %d", ids[i]);
            Py_DECREF(idsarr);
            Py_DECREF(posarr);
            throw_error_already_set();
        }
    }

    IdList result = (hash.*func)(r, pos, n, ids);

    Py_DECREF(idsarr);
    Py_DECREF(posarr);
    npy_intp dims[1];
    dims[0] = result.size();
    PyObject* arr = PyArray_SimpleNew(1,dims,NPY_UINT32);
    if (!arr) throw_error_already_set();
    if (!result.empty()) memcpy(PyArray_DATA(arr), 
                                &result[0],
                                result.size()*sizeof(Id));
    return arr;
}

static PyObject* hash_find_within(SpatialHash& hash,
                                  float r,
                                  PyObject* pos,
                                  PyObject* ids,
                                  bool reuse_voxels) {

    return reuse_voxels ? hash_find(hash, r, pos, ids, &SpatialHash::find_within)
                        : hash_find(hash, r, pos, ids, &SpatialHash::findWithin);
}

static PyObject* hash_find_nearest(SpatialHash& hash,
                                   int k,
                                   PyObject* pos,
                                   PyObject* ids) {

    return hash_find(hash, k, pos, ids, &SpatialHash::findNearest);
}

static PyObject* hash_find_contacts(SpatialHash& hash,
                                    float r,
                                    PyObject* posobj,
                                    PyObject* idsobj,
                                    bool reuse_voxels) {

    PyObject* posarr = PyArray_FromAny(posobj,
                PyArray_DescrFromType(NPY_FLOAT32),
                2, 2, NPY_C_CONTIGUOUS | NPY_ALIGNED,
                NULL);
    if (!posarr) throw_error_already_set();
    Id n = PyArray_DIM(posarr,0);

    const Id* ids = NULL;
    PyObject* idsarr = NULL;
    if (idsobj != Py_None) {
        idsarr = PyArray_FromAny(idsobj,
                    PyArray_DescrFromType(NPY_UINT32),
                    1, 1, NPY_C_CONTIGUOUS | NPY_ALIGNED,
                    NULL);
        if (!idsarr) {
            Py_DECREF(posarr);
            throw_error_already_set();
        }
        ids = (const Id*)PyArray_DATA(idsarr);
        for (Py_ssize_t i=0, m=PyArray_DIM(idsarr, 0); i<m; i++) {
            if (ids[i]>=n) {
                Py_DECREF(posarr);
                PyErr_Format(PyExc_ValueError, "id out of bounds: %d", ids[i]);
                throw_error_already_set();
            }
        }
        n = PyArray_DIM(idsarr, 0);
    }

    const float* pos = (const float*)PyArray_DATA(posarr);
    SpatialHash::contact_array_t contacts;

    if (reuse_voxels) {
        // drop the GIL here?
        hash.findContactsReuseVoxels(r, pos, n, ids, &contacts);
    } else {
        hash.findContacts(r, pos, n, ids, &contacts);
    }
    Py_XDECREF(idsarr);
    Py_DECREF(posarr);

    npy_intp dim = contacts.count;
    std::for_each(contacts.d2, contacts.d2+dim, [](float& x) {x=std::sqrt(x);});

    PyObject* iarr = PyArray_SimpleNew(1,&dim,NPY_UINT32);
    PyObject* jarr = PyArray_SimpleNew(1,&dim,NPY_UINT32);
    PyObject* darr = PyArray_SimpleNew(1,&dim,NPY_FLOAT);
    memcpy(PyArray_DATA(iarr), contacts.i, dim*sizeof(*contacts.i));
    memcpy(PyArray_DATA(jarr), contacts.j, dim*sizeof(*contacts.j));
    memcpy(PyArray_DATA(darr), contacts.d2,dim*sizeof(*contacts.d2));

    PyObject* result = PyTuple_New(3);
    PyTuple_SET_ITEM(result, 0, iarr);
    PyTuple_SET_ITEM(result, 1, jarr);
    PyTuple_SET_ITEM(result, 2, darr);
    return result;
}

namespace {
    // exclusions of (Id a, Id b) pairs; include both (a, b) and (b, a) in
    // the high and low order bits.
    typedef std::unordered_set<uint64_t> SpatialHashExclusions;

    struct Exclusions : SpatialHashExclusions {
        void add(Id i, Id j) {
            uint64_t key1(i), key2(j);
            key1 <<= 32;
            key2 <<= 32;
            key1 |= j;
            key2 |= i;
            insert(key1);
            insert(key2);
        }
    };
}

static PyObject* hash_find_pairlist(SpatialHash& hash,
                                    float r,
                                    Exclusions const& excl,
                                    bool reuse_voxels) {

    SpatialHash::contact_array_t contacts;
    if (!reuse_voxels) {
        hash.voxelize(r);
    }
    hash.findPairlistReuseVoxels(r, excl, &contacts);

    npy_intp dim = contacts.count;
    std::for_each(contacts.d2, contacts.d2+dim, [](float& x) {x=std::sqrt(x);});

    PyObject* iarr = PyArray_SimpleNew(1,&dim,NPY_UINT32);
    PyObject* jarr = PyArray_SimpleNew(1,&dim,NPY_UINT32);
    PyObject* darr = PyArray_SimpleNew(1,&dim,NPY_FLOAT);
    memcpy(PyArray_DATA(iarr), contacts.i, dim*sizeof(*contacts.i));
    memcpy(PyArray_DATA(jarr), contacts.j, dim*sizeof(*contacts.j));
    memcpy(PyArray_DATA(darr), contacts.d2,dim*sizeof(*contacts.d2));

    PyObject* result = PyTuple_New(3);
    PyTuple_SET_ITEM(result, 0, iarr);
    PyTuple_SET_ITEM(result, 1, jarr);
    PyTuple_SET_ITEM(result, 2, darr);
    return result;
}

namespace desres { namespace msys {
    void export_spatial_hash() {

        class_<Exclusions>("SpatialHashExclusions", init<>())
            .def("add", &Exclusions::add)
            ;

        class_<SpatialHash>("SpatialHash", no_init)
            .def("__init__", make_constructor(
                        hash_new, default_call_policies(),
                        (arg("pos"), arg("ids"), arg("box")=object())))
            .def("voxelize", &SpatialHash::voxelize, return_internal_reference<>())
            .def("findWithin", hash_find_within,
                    (arg("r"), 
                     arg("pos"), 
                     arg("ids"), 
                     arg("reuse_voxels")=false))
            .def("findNearest", hash_find_nearest,
                    (arg("k"), 
                     arg("pos"), 
                     arg("ids")))
            .def("findContacts", hash_find_contacts,
                    (arg("r"),
                     arg("pos"),
                     arg("ids")=object(),
                     arg("reuse_voxels")=false))
            .def("findPairlist", hash_find_pairlist,
                    (arg("r"),
                     arg("excl"),
                     arg("reuse_voxels")=false))
            ;
    }
}}

