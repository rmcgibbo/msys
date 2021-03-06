#include "wrap_obj.hxx"
#include "term_table.hxx"
#include "override.hxx"

using namespace desres::msys;

namespace {

    list list_terms(TermTable& table) {
        return to_python(table.terms());
    }
    list list_atoms(TermTable& table, Id i) {
        return to_python(table.atoms(i));
    }

    Id add_term(TermTable& table, object atoms, object param) {
        Id id=BadId;
        if (param.ptr()!=Py_None) id=extract<Id>(param);
        list L(atoms);
        IdList ids(len(L));
        for (unsigned i=0; i<ids.size(); i++) ids[i]=extract<Id>(L[i]);
        return table.addTerm(ids, id);
    }

    void set_param(TermTable& table, Id term, object param) {
        Id id=BadId;
        if (param.ptr()!=Py_None) id=extract<Id>(param);
        table.setParam(term,id);
    }

    PyObject* term_prop_type(TermTable& table, Id col) {
        return from_value_type(table.termPropType(col));
    }
    Id add_term_prop( TermTable& table, String const& name, object type ) {
        return table.addTermProp(name, as_value_type(type));
    }

    /* TODO: permit col to be provided as string */
    object get_term_prop(TermTable& p, Id row, Id col) {
        return from_value_ref(p.termPropValue(row,col));
    }
    void set_term_prop(TermTable& p, Id row, Id col, object newval) {
        to_value_ref(newval, p.termPropValue(row,col));
    }

    object get_prop(TermTable& p, Id row, Id col) {
        return from_value_ref(p.propValue(row,col));
    }
    void set_prop(TermTable& p, Id row, Id col, object newval) {
        to_value_ref(newval, p.propValue(row,col));
    }

    list find_all(TermTable& p, list ids) {
        return to_python(p.findWithAll(ids_from_python(ids)));
    }
    list find_any(TermTable& p, list ids) {
        return to_python(p.findWithAny(ids_from_python(ids)));
    }
    list find_only(TermTable& p, list ids) {
        return to_python(p.findWithOnly(ids_from_python(ids)));
    }
    list find_exact(TermTable& p, list ids) {
        return to_python(p.findExact(ids_from_python(ids)));
    }
}

namespace desres { namespace msys { 

    void export_term() {

        enum_<Category>("Category")
            .value("none", NO_CATEGORY)
            .value("bond", BOND)
            .value("constraint", CONSTRAINT)
            .value("virtual", VIRTUAL)
            .value("polar", POLAR)
            .value("nonbonded", NONBONDED)
            .value("exclusion", EXCLUSION)
            ;

        def("parse_category", parse);
        def("print_category", print);

        class_<TermTable, TermTablePtr>("TermTablePtr", no_init)
            .def("__eq__",      list_eq<TermTablePtr>)
            .def("__ne__",      list_ne<TermTablePtr>)
            .def("__hash__",    obj_hash<TermTablePtr>)
            .def("destroy",     &TermTable::destroy)
            .def("system",      &TermTable::system)
            .def("atomCount",   &TermTable::atomCount)
            .def("termCount",   &TermTable::termCount)
            .def_readwrite("category", &TermTable::category)
            .def("name",        &TermTable::name)
            .def("rename",      &TermTable::rename)
            .def("terms",       list_terms)
            .def("addTerm",     add_term)
            .def("hasTerm",     &TermTable::hasTerm)
            .def("delTerm",     &TermTable::delTerm)
            .def("atoms",       list_atoms)
            .def("atom",        &TermTable::atom)
            .def("params",      &TermTable::params)
            .def("param",       &TermTable::param)
            .def("setParam",    set_param)

            /* Table properties */
            .def("tableProps",  &TermTable::tableProps, return_ptr())

            /* param properties */
            .def("getProp",     get_prop)
            .def("setProp",     set_prop)

            /* term properties */
            .def("termPropCount",&TermTable::termPropCount)
            .def("termPropName", &TermTable::termPropName)
            .def("termPropIndex",&TermTable::termPropIndex)
            .def("termPropType", term_prop_type)
            .def("addTermProp",  add_term_prop)
            .def("delTermProp",  &TermTable::delTermProp)
            .def("getTermProp",  get_term_prop)
            .def("setTermProp",  set_term_prop)

            /* lookup terms based on atom */
            .def("delTermsWithAtom",    &TermTable::delTermsWithAtom)
            .def("findWithAll", find_all)
            .def("findWithAny", find_any)
            .def("findWithOnly",find_only)
            .def("findExact"  , find_exact)

            /* coalesce */
            .def("coalesce",    &TermTable::coalesce)

            /* overrides */
            .def("overrides",   &TermTable::overrides)

            /* misc */
            .def("resetParams", &TermTable::resetParams)
            .def("replaceWithSortedTerms", ReplaceTableWithSortedTerms)
            ;
    }

}}
