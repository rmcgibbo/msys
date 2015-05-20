#include "wrap_obj.hxx"
#include "schema.hxx"
#include "mae.hxx"
#include "dms.hxx"
#include "pdb.hxx"
#include "mol2.hxx"
#include "xyz.hxx"
#include "io.hxx"
#include "amber.hxx"
#include "sdf.hxx"

namespace {

    SystemPtr import_mae_from_buffer(PyObject* obj, bool ignore_unrecognized,
                                                    bool structure_only) {
        Py_buffer view[1];
        if (PyObject_GetBuffer(obj, view, PyBUF_ND)) {
            throw_error_already_set();
        }
        boost::shared_ptr<Py_buffer> ptr(view, PyBuffer_Release);
        const char* bytes = reinterpret_cast<const char *>(view->buf);
        return ImportMAEFromBytes(bytes, view->len, 
                                  ignore_unrecognized,
                                  structure_only);
    }

    SystemPtr import_dms_from_buffer( PyObject* obj, bool structure_only ) {
        Py_buffer view[1];
        if (PyObject_GetBuffer(obj, view, PyBUF_ND)) {
            throw_error_already_set();
        }
        boost::shared_ptr<Py_buffer> ptr(view, PyBuffer_Release);
        char* bytes = reinterpret_cast<char *>(view->buf);
        return ImportDMSFromBytes(bytes, view->len, structure_only);
    }

    SystemPtr import_sdf_from_buffer( PyObject* obj ) {
        Py_buffer view[1];
        if (PyObject_GetBuffer(obj, view, PyBUF_ND)) {
            throw_error_already_set();
        }
        boost::shared_ptr<Py_buffer> ptr(view, PyBuffer_Release);
        char* bytes = reinterpret_cast<char *>(view->buf);
        std::istringstream file;
        file.rdbuf()->pubsetbuf(const_cast<char *>(bytes), view->len);
        return ImportSdfFromStream(file);
    }

    list import_mol2_many(std::string const& path) {
        std::vector<SystemPtr> mols = ImportMol2Many(path);
        list L;
        for (unsigned i=0; i<mols.size(); i++) {
            L.append(object(mols[i]));
        }
        return L;
    }

    std::string export_sdf_bytes(SystemPtr mol) {
        std::stringstream ss;
        ExportSdf(mol,ss);
        return ss.str();
    }

    LoadIteratorPtr load_iterator_create(std::string const& path,
                                         bool structure_only) {
        return LoadIterator::create(path, structure_only);
    }
    SystemPtr load_iterator_next(LoadIterator& iter) {
        return iter.next();
    }

    void save(SystemPtr mol, std::string const& path, Provenance const& prov,
              bool append, bool structure_only) {
        unsigned flags = 0;
        if (append) flags |= SaveOptions::Append;
        if (structure_only) flags |= SaveOptions::StructureOnly;
        Save(mol, path, prov, flags);
    }

    SystemPtr import_dms(const std::string& path, bool structure_only=false) {
        return ImportDMS(path, structure_only);
    }

    SystemPtr load(std::string const& path, bool structure_only,
                   FileFormat* opt_format) {
        return Load(path, structure_only, opt_format);
    }

}

namespace desres { namespace msys { 

    void export_io() {
        
        enum_<DMSExport::Flags>("DMSExportFlags")
            .value("Default",           DMSExport::Default)
            .value("Append",            DMSExport::Append)
            .value("StructureOnly",     DMSExport::StructureOnly)
            .value("Unbuffered",        DMSExport::Unbuffered)
            ;

        enum_<MaeExport::Flags>("MaeExportFlags")
            .value("Default",           MaeExport::Default)
            .value("StructureOnly",     MaeExport::StructureOnly)
            //.value("CompressForcefield",MaeExport::CompressForcefield)
            .value("Append",            MaeExport::Append)
            ;

        enum_<Mol2Export::Flags>("Mol2ExportFlags")
            .value("Default",           Mol2Export::Default)
            .value("Append",            Mol2Export::Append)
            ;

        enum_<PDBExport::Flags>("PDBExportFlags")
            .value("Default",           PDBExport::Default)
            .value("Append",            PDBExport::Append)
            ;

        class_<LoadIterator, LoadIteratorPtr, boost::noncopyable>("LoadIterator", no_init)
            .def("create", load_iterator_create).staticmethod("create")
            .def("next", load_iterator_next)
            ;

        def("ImportDMS", import_dms);
        def("ImportDMSFromBuffer", import_dms_from_buffer);
        def("ExportDMS", ExportDMS);
        def("ImportMAE", ImportMAE);
        def("ImportMAEFromBuffer", import_mae_from_buffer);
        def("ExportMAE", ExportMAE);
        def("ExportMAEContents", ExportMAEContents);
        def("ImportPDB", ImportPDB);
        def("ExportPDB", ExportPDB);
        def("ImportPrmTop", ImportPrmTop);
        def("ImportCrdCoordinates", ImportCrdCoordinates);
        def("ImportPDBCoordinates", ImportPDBCoordinates);
        def("ImportMOL2", ImportMol2);
        def("ImportMOL2Many", import_mol2_many);
        def("ExportMOL2", ExportMol2);
        def("ImportXYZ", ImportXYZ);
        def("ImportSDF", ImportSdf);
        def("ImportSDFFromBuffer", import_sdf_from_buffer);

        def("ExportSDFBytes", export_sdf_bytes);
        def("Load", load,
                (arg("path"),
                 arg("structure_only")=false,
                 arg("opt_format")=object()));
        def("Save", save);


    }
}}
