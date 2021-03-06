#include "../ff.hxx"
#include <cmath>

namespace {

    typedef std::vector<double> Param;

    static void convert_sig_eps( double sij, double eij, double sf, Param& p) {
        sf *= eij * 4;
        double s3 = sij*sij*sij;
        double s6=s3*s3;
        double s12=s6*s6;
        p[0]=sf*s12;
        p[1]=sf*s6;
    }

    static void combine_geometric( const Param& vi, const Param& vj, double sf,
                                   Param& p ) {
        double sij = sqrt(vi[0]*vj[0]);
        double eij = sqrt(vi[1]*vj[1]);
        convert_sig_eps( sij, eij, sf, p );
    }

    static void combine_arith_geom( const Param& vi, const Param& vj, double sf,
                                   Param& p ) {
        double sij = 0.5*(vi[0]+vj[0]);
        double eij = sqrt(vi[1]*vj[1]);
        convert_sig_eps( sij, eij, sf, p );
    }

    static void combine_lb_geom( const Param& vi, const Param& vj, double sf,
                                 Param& p ) {

       /* Convert type i, alpha==0 signifies that parameters are A,B */
       double Ai, Bi, Ci;
       double Aj, Bj, Cj;
       if (vi[0]==0) {
           Ai = vi[0];
           Bi = vi[1];
           Ci = 0;
       } else {
           Ai = (6.*vi[1]*exp(vi[0]))/(vi[0] - 6.);
           Bi = vi[2] / vi[0];
           Ci = (pow(vi[0],7)*vi[1])/(vi[0] - 6.);
       }

       /* Convert type j, alpha==0 signifies that parameters are A,B  */
       if (vj[0]==0) {
           Aj = vj[0];
           Bj = vj[1];
           Cj = 0;
       } else {
           Aj = (6.*vj[1]*exp(vj[0]))/(vj[0] - 6.);
           Bj = vj[2] / vj[0];
           Cj = (pow(vj[0],7)*vj[1])/(vj[0] - 6.);
       }

       p[0] = sf * sqrt(Ai*Aj);
       p[1] =      0.5*(Bi+Bj);
       p[2] = sf * sqrt(Ci*Cj);
    }   

#ifdef DESMOND_USE_SCHRODINGER_MMSHARE
    struct PairData
    {
      std::string         schedule;
      std::vector<double> cs;
    };
#endif

    typedef void (*combine_func)( const Param& vi, const Param& vj, double sf,
                                             Param& p );

    template <bool alchemical>
    struct Pairs : public Ffio {

        void apply( SystemPtr h,
                    const Json& blk,
                    const SiteMap& sitemap,
                    const VdwMap& vdwmap ) const {

            const char * pname;
            combine_func combine = NULL;

            if (vdwmap.funct()=="lj12_6_sig_epsilon" || 
                vdwmap.funct()=="polynomial_cij") {
                pname="pair_12_6_es";
                if (vdwmap.rule()=="geometric") {
                    combine=combine_geometric;
                } else if (vdwmap.rule()=="arithmetic/geometric") {
                    combine=combine_arith_geom;
                }
            } else if (vdwmap.funct()=="exp_6x") {
                pname="pair_exp_6_es";
                if (vdwmap.rule()=="lb/geometric") {
                    combine=combine_lb_geom;
                }
            } else {
                FFIO_ERROR("Unsupported ffio_funct '" << vdwmap.funct()
                        << "' for ffio_pairs");
            }
            if (!combine) {
                FFIO_ERROR("Unsupported ffio_comb_rule '" 
                    << vdwmap.rule() << "' for ffio_funct '" << vdwmap.funct()
                    << "' in ffio_pairs.");
            }

            std::string prefix;
            if (alchemical) prefix = "alchemical_";
            TermTablePtr table = AddTable(h,prefix+pname);
            ParamMap map(table->params(), blk);
            Id nprops = table->params()->propCount();
            if (alchemical) nprops /= 2;

            const Json& ai = blk.get("ffio_ai");
            const Json& aj = blk.get("ffio_aj");
            const Json& fn = blk.get("ffio_funct");
#ifdef DESMOND_USE_SCHRODINGER_MMSHARE
            const Json& sc = blk.get("ffio_schedule");
#endif
            const Json& c1 = blk.get("ffio_c1");
            const Json& c2 = blk.get("ffio_c2");
            const Json& c1B = blk.get("ffio_c1B");
            const Json& c2B = blk.get("ffio_c2B");

            /* We need to deal with multiple pair entries.  We initialize
             * skipped to the full set of rows.  Each time through the
             * loop, we only process rows that were previously skipped.
             * If we process a row, we take it off the skipped list.  We
             * skip a row if its parameters would collide with parameters
             * that have already been determined for that pair of atoms. */
            std::set<int> skipped;
            for (int i=0; i<blk.get("__size__").as_int(); i++) {
                skipped.insert(i);
            }

            do {
              IdList ids(2);
#ifdef DESMOND_USE_SCHRODINGER_MMSHARE
              typedef std::map<IdList, PairData> PairHash;
#else
              typedef std::map<IdList, std::vector<double> > PairHash;
#endif
              PairHash pairhash;
              PairHash pairhashB;
  
              int i,n=blk.get("__size__").as_int();
              //if (n-skipped.size()) {
                  //printf("found %d duplicate pairs\n", (int)skipped.size());
              //}
              for (i=0; i<n; i++) {
                /* do this row only if we skipped it last time. */
                if (!skipped.count(i)) continue;
                ids[0]=ai.elem(i).as_int();
                ids[1]=aj.elem(i).as_int();
                std::pair<PairHash::iterator,bool> r, rB;
#ifdef DESMOND_USE_SCHRODINGER_MMSHARE
                r=pairhash.insert(std::make_pair( ids, PairData() ));
                std::string&         sched  = r.first->second.schedule;
                std::vector<double>& params = r.first->second.cs;
#else
                r=pairhash.insert(std::make_pair( ids, std::vector<double>()));
                std::vector<double>& params = r.first->second;
#endif
                std::vector<double>* paramsB = NULL;
                if (r.second) {
                    /* first time seeing this pair */
                    params.clear();
                    params.insert(params.begin(), nprops, HUGE_VAL);
                }
                if (alchemical) {
#ifdef DESMOND_USE_SCHRODINGER_MMSHARE
                    rB=pairhashB.insert(std::make_pair( ids, PairData() ));
                    paramsB = &rB.first->second.cs;
#else
                    rB=pairhashB.insert(std::make_pair( ids, std::vector<double>()));
                    paramsB = &rB.first->second;
#endif
                    if (rB.second) {
                        ///* first time seeing this alchemical pair */
                        paramsB->clear();
                        paramsB->insert(paramsB->begin(), nprops, HUGE_VAL);
                    }
                }
                std::string f = fn.elem(i).as_string();
#ifdef DESMOND_USE_SCHRODINGER_MMSHARE
                const char* s = sc.valid() ? sc.elem(i).as_string() : "NULL";
                sched = s;
#endif
                to_lower(f);
                if (f=="coulomb" || f=="coulomb_scale") {
                    if (params.back()!=HUGE_VAL) continue;
                    Id iatom = sitemap.site(ai.elem(i).as_int());
                    Id jatom = sitemap.site(aj.elem(i).as_int());
                    double qscale = c1.elem(i).as_float();
                    double qi = h->atom(iatom).charge;
                    double qj = h->atom(jatom).charge;
                    params.back() = qscale * qi * qj;

                    if (alchemical) {
                        double qscale = c1B.elem(i).as_float();
                        double qiB = vdwmap.chargeB(ai.elem(i).as_int());
                        double qjB = vdwmap.chargeB(aj.elem(i).as_int());
                        if (qiB==HUGE_VAL) qiB=qi;
                        if (qjB==HUGE_VAL) qjB=qj;
                        paramsB->back() = qscale * qiB * qjB;
                    }

                } else if (f=="coulomb_qij") {
                    if (params.back()!=HUGE_VAL) continue;
                    params.back() = c1.elem(i).as_float();
                    if (alchemical) {
                        paramsB->back() = c1B.elem(i).as_float();
                    }

                } else if (f=="lj" || f=="lj_scale") {
                    if (params[0]!=HUGE_VAL) continue;
                    int indi = ai.elem(i).as_int();
                    int indj = aj.elem(i).as_int();
                    const VdwType& itype = vdwmap.type(indi);
                    const VdwType& jtype = vdwmap.type(indj);
                    if (vdwmap.has_combined(itype, jtype)) {
                        const VdwParam& p = vdwmap.param(itype,jtype);
                        /* DESRESCode#1634 - apply the LJ scale factor to
                         * the combined LJ parameter */
                        double lscale = c1.elem(i).as_float();
                        combine( p, p, lscale, params );
                    } else {
                        const VdwParam& iparam = vdwmap.param(itype);
                        const VdwParam& jparam = vdwmap.param(jtype);
                        double lscale = c1.elem(i).as_float();
                        combine( iparam, jparam, lscale, params );
                    }

                    if (alchemical) {
                        const VdwType& itypeB = vdwmap.typeB(indi);
                        const VdwType& jtypeB = vdwmap.typeB(indj);
                        if (vdwmap.has_combined(itypeB, jtypeB)) {
                            const VdwParam& p = vdwmap.param(itypeB,jtypeB);
                            double lscale = c1B.elem(i).as_float();
                            combine( p, p, lscale, *paramsB );
                        } else {
                            const VdwParam& iparam = 
                                itypeB.size() ? vdwmap.param(itypeB)
                                              : vdwmap.param(itype);
                            const VdwParam& jparam = 
                                jtypeB.size() ? vdwmap.param(jtypeB)
                                              : vdwmap.param(jtype);
                            double lscale = c1B.elem(i).as_float();
                            combine( iparam, jparam, lscale, *paramsB );
                        }
                    }

                } else if (f=="lj12_6_sig_epsilon") {
                    if (params[0]!=HUGE_VAL) continue;
                    convert_sig_eps( c1.elem(i).as_float(),
                                     c2.elem(i).as_float(),
                                     1.0,
                                     params );
                    if (alchemical) convert_sig_eps( 
                                     c1B.elem(i).as_float(),
                                     c2B.elem(i).as_float(),
                                     1.0,
                                     *paramsB );

                } else {
                    FFIO_ERROR("Unsupported ffio_funct " << f 
                            << "' in ffio_pairs");
                }
                skipped.erase(i);
              }
            
              PairHash::iterator iter, iterB;
              iterB = pairhashB.begin();
              for (iter=pairhash.begin(); iter!=pairhash.end(); ++iter) {
                  if (alchemical) {
                      /* extend with B state */
#ifdef DESMOND_USE_SCHRODINGER_MMSHARE
                      iter->second.cs.insert(iter->second.cs.end(),
                                            iterB->second.cs.begin(), 
                                            iterB->second.cs.end());
#else
                      iter->second.insert(iter->second.end(),
                                          iterB->second.begin(), 
                                          iterB->second.end());
#endif
                      ++iterB;
                  }
                  /* we may have had an mae file with and LJ pair and no
                   * corresponding ES pair, or vice versa, in which case
                   * we would still have the HUGE_VAL sentinel values in
                   * the params.  Convert those back to 0.0. */
#ifdef DESMOND_USE_SCHRODINGER_MMSHARE
                  for (unsigned i=0; i<iter->second.cs.size(); i++) {
                      if (iter->second.cs[i]==HUGE_VAL) {
                          iter->second.cs[i]=0;
#else
                  for (unsigned i=0; i<iter->second.size(); i++) {
                      if (iter->second[i]==HUGE_VAL) {
                          iter->second[i]=0;
#endif
                      }
                  }
#ifdef DESMOND_USE_SCHRODINGER_MMSHARE
                  Id A = map.add(iter->second.cs);
                  sitemap.addUnrolledTerms( table, A, iter->first, 0, iter->second.schedule == "NULL" ? 0 : iter->second.schedule.c_str() );
#else
                  Id A = map.add(iter->second);
                  sitemap.addUnrolledTerms( table, A, iter->first );
#endif
              }
            } while (skipped.size());
        }
    };

    RegisterFfio<Pairs<false> > _1("ffio_pairs");
    RegisterFfio<Pairs<true> > _2("ffio_pairs_alchemical");
}

