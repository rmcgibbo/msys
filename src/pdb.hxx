#ifndef desres_msys_pdb_hxx
#define desres_msys_pdb_hxx

#include "io.hxx"

namespace desres { namespace msys {

    SystemPtr ImportPDB( std::string const& path );
    SystemPtr ImportWebPDB( std::string const& code);
    std::string FetchPDB(std::string const& code);
    LoadIteratorPtr PDBIterator(std::string const& path);

    void ImportPDBCoordinates( SystemPtr mol, std::string const& path );

    struct PDBExport {
        enum Flags { Default            = 0 
                   , Append             = 1 << 0
                   , Reorder            = 1 << 1
        };
    };
    void ExportPDB(SystemPtr mol, std::string const& path, unsigned flags=0);

    void ImportPDBUnitCell(double A, double B, double C,
                           double alpha, double beta, double gamma,
                           double* cell_3x3);

    void ExportPDBUnitCell(const double* cell_3x3,
                           double *A, double *B, double *C,
                           double *alpha, double *beta, double *gamma);

}}

#endif
