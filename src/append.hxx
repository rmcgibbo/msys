#ifndef desres_msys_append_hxx
#define desres_msys_append_hxx

#include "term_table.hxx"

namespace desres { namespace msys {

    /* Append given parameters in src to dst, expanding the set of properties
     * as necessary.  Return the ids of the newly added parameters. */
    IdList AppendParams(ParamTablePtr dst, ParamTablePtr src,
                        IdList const& params );

    /* Append given terms in src to dst, using the mapping from atom id 
     * in src to atom id in dst provided by idmap.  Return the ids of the 
     * newly created terms. */
    IdList AppendTerms( TermTablePtr dst, TermTablePtr src, 
                        IdList const& idmap,
                        IdList const& terms );

    /* Append given terms in src to dst, using the mapping from atom id 
     * in src to atom id in dst provided by idmap, and the provided
     * mapping from src params to dst params.  No params will be added
     * to dst.  Return the ids of the newly created terms. */
    IdList AppendTerms( TermTablePtr dst, TermTablePtr src, 
                        IdList const& idmap,
                        IdList const& terms,
                        IdList const& pmap );

    /* Append structure and term tables from src into dst, using 
     * AppendParams to extend the parameter tables, and expanding
     * the set of term properties as necessary.  Extra tables in src
     * replace those with the same name in dst.  Return the ids
     * of the newly added atoms. */
    IdList AppendSystem( SystemPtr dst, SystemPtr src );

}}

#endif
