#include "analyze.hxx"
#include "sssr.hxx"
#include <boost/python.hpp>

using namespace desres::msys;
using namespace boost::python;

namespace {
    void assign_1(SystemPtr mol) {
        AssignBondOrderAndFormalCharge(mol);
    }
    void assign_2(SystemPtr mol, IdList const& ids) {
        AssignBondOrderAndFormalCharge(mol, ids);
    }
    void assign_3(SystemPtr mol, IdList const& ids, int total_charge) {
        AssignBondOrderAndFormalCharge(mol, ids, total_charge);
    }
    list get_sssr(SystemPtr mol, IdList const& ids, bool all_relevant) {
        MultiIdList rings = GetSSSR(mol, ids, all_relevant);
        list L;
        for (unsigned i=0; i<rings.size(); i++) L.append(rings[i]);
        return L;
    }
}

namespace desres { namespace msys { 

    void export_analyze() {
        def("AssignBondOrderAndFormalCharge", assign_1);
        def("AssignBondOrderAndFormalCharge", assign_2);
        def("AssignBondOrderAndFormalCharge", assign_3);
        def("GetSSSR", get_sssr);
    }
}}
