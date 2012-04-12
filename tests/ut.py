#!/usr/bin/env python2.7

import os, sys, unittest
TMPDIR=os.getenv('TMPDIR', 'objs/Linux/x86_64')
sys.path.insert(0,os.path.join(TMPDIR, 'lib', 'python'))
import msys

class TestMain(unittest.TestCase):

    def testAtom(self):
        m=msys.CreateSystem()
        a1=m.addAtom()
        a2=m.addAtom()
        self.assertTrue(a1.system==m)
        self.assertTrue(a2.system==m)
        self.assertEqual(a2.system.atoms[0], a1)
        self.assertEqual(a1.system.atoms[1], a2)
        self.assertNotEqual(m.atom(0), m.atom(1))

        # FIXME: hmm, maybe fetching m.atom(0) ought to throw after the
        # atom has been removed.  
        m.atom(0).remove()
        self.assertFalse(m.atom(0) in m.atoms)

        m2=msys.CreateSystem()
        a3=m2.addAtom()
        self.assertNotEqual(a1,a3)
        self.assertEqual(a3,a3)
        self.assertEqual(a3,m2.atom(0))

        res=a1.residue
        self.assertEqual(m.residues[0], res)
        rnew = m.addResidue()
        self.assertNotEqual(rnew, a1.residue)
        a1.residue = rnew
        self.assertEqual(rnew, a1.residue)

    def testGlue(self):
        m=msys.CreateSystem()
        m.addAtom()
        m.addAtom()
        m.addAtom()

        with self.assertRaises(RuntimeError): m.addGluePair(1,1)
        with self.assertRaises(RuntimeError): m.addGluePair(1,10)
        with self.assertRaises(RuntimeError): m.addGluePair(10,1)

        self.assertEqual(m.gluePairs(), [])
        self.assertFalse(m.hasGluePair(1,2))
        self.assertFalse(m.hasGluePair(2,1))
        m.addGluePair(2,1)
        m.addGluePair(0,1)
        self.assertTrue(m.hasGluePair(1,0))
        self.assertTrue(m.hasGluePair(1,2))
        self.assertTrue(m.hasGluePair(2,1))
        self.assertEqual(m.gluePairs(), [(0,1),(1,2)])
        m2=m.clone('index 1 2')
        m3=m2.clone()
        m3.append(m)
        m.delGluePair(2,1)
        self.assertFalse(m.hasGluePair(1,2))
        self.assertFalse(m.hasGluePair(2,1))
        self.assertEqual(m2.gluePairs(), [(0,1)])
        self.assertEqual(m3.gluePairs(), [(0,1), (2,3),(3,4)])

    def testSelectOnRemoved(self):
        m=msys.CreateSystem()
        m.addAtom()
        m.addAtom().atomic_number=17
        m.addAtom()
        for a in m.select('atomicnumber 17'): a.remove()
        self.assertEqual(0, len(m.select('atomicnumber 17')))

    def testCoalesce(self):
        m=msys.CreateSystem()
        a=m.addAtom()
        table=m.addTableFromSchema('posre_harm')
        p1=table.params.addParam()
        p2=table.params.addParam()
        p3=table.params.addParam()
        p3['fcx'] = 32


        t1=table.addTerm([a], p1)
        t2=table.addTerm([a], p2)
        t3=table.addTerm([a], p3)
        t4=table.addTerm([a])
        t4.paramB = p2

        self.assertFalse( t1.param==t2.param)
        self.assertFalse( t1.param==t3.param)

        table.coalesce()
        self.assertTrue( t1.param==t2.param)
        self.assertTrue( t1.param==p1)
        self.assertTrue( t2.param==p1)
        self.assertFalse( t1.param==t3.param)
        self.assertTrue( t3.param==p3)

        self.assertTrue(t4.param is None)
        self.assertTrue(t4.paramB == p1)


    def testAtomProps(self):
        m=msys.CreateSystem()
        a1=m.addAtom()
        F, I, S = 'F', 'I', 'S'
        for p,t in zip((F, I, S), (float, int, str)):
            m.addAtomProp(p,t)
            self.assertTrue(p in m.atom_props)
            self.assertEqual(m.atomPropType(p), t)
        self.assertEqual(len(m.atom_props), 3)
        a2=m.addAtom()

        a1.charge = 3.5
        self.assertEqual(a1.charge, 3.5)
        self.assertEqual(m.atom(a1.id).charge, a1.charge)
        self.assertEqual(a1[F], 0)
        self.assertEqual(a1[I], 0)
        self.assertEqual(a1[S], "")

        a1[F]=32.5
        a1[I]=42
        a1[S]="justinrocks"
        self.assertEqual(a1[F], 32.5)
        self.assertEqual(a1[I], 42)
        self.assertEqual(a1[S], "justinrocks")

        with self.assertRaises(KeyError):
            a1['foobar'] = 32

        self.assertTrue(hasattr(a2, 'charge'))
        self.assertTrue('F'in a2)
        self.assertFalse('foobar' in a2)

        m.delAtomProp('F')
        self.assertFalse('F'in a2)
        self.assertEqual([m.atomPropType(n) for n in m.atom_props], 
                [int, str])


    def testBond(self):
        m=msys.CreateSystem()
        a1=m.addAtom()
        a2=m.addAtom()
        a3=m.addAtom()
        b=a2.addBond(a3)
        self.assertEqual(b.system, m)
        self.assertEqual(b.first, a2)
        self.assertEqual(b.second, a3)
        b.order=32.5
        self.assertEqual(b.order, 32.5)
        self.assertEqual(len(m.bonds),1)

        first, second = b.atoms
        self.assertEqual(first, a2)
        self.assertEqual(second, a3)

        self.assertEqual([a for a in a1.bonded_atoms], [])
        self.assertEqual([a for a in a2.bonded_atoms], [a3])
        self.assertEqual([a for a in a3.bonded_atoms], [a2])

        b.remove()
        self.assertEqual(len(m.bonds),0)

        b1=a1.addBond(a2)
        self.assertEqual(len(a2.bonds),1)
        self.assertEqual(b1, m.findBond(a1,a2))
        self.assertEqual(b1, a1.findBond(a2))
        self.assertEqual(b1, a2.findBond(a1))
        self.assertEqual(None, m.findBond(a1,a3))

        self.assertEqual(a2.nbonds, 1)

        b.remove()
        b.remove()
        b.remove()
        self.assertEqual(len(a2.bonds),1)

        m.delBonds(m.bonds)
        self.assertEqual(len(m.bonds), 0)
        m.delAtoms(m.atoms)
        self.assertEqual(len(m.atoms), 0)

        self.assertEqual(len(m.residues), 3)
        m.delResidues(m.residues[2:])
        self.assertEqual(len(m.residues), 2)
        m.delResidues(m.residues[0:1])
        self.assertEqual(len(m.residues), 1)
        m.delChains(m.chains)
        self.assertEqual(len(m.chains), 0)

    def testRemove(self):
        m=msys.CreateSystem()
        r=m.addResidue()
        for i in range(10000):
            r.addAtom()
        self.assertEqual(r.natoms, 10000)
        r.remove()
        r.remove()
        r.remove()
        self.assertEqual(len(m.atoms), 0)

        c=m.addChain()
        for i in range(10000):
            c.addResidue()
        self.assertEqual(c.nresidues, 10000)

        c.remove()
        c.remove()
        c.remove()
        self.assertEqual(len(m.residues), 0)
        self.assertEqual(c.nresidues, 0)

    def testResidue(self):
        m=msys.CreateSystem()
        r=m.addResidue()
        a1=r.addAtom()
        a2=r.addAtom()
        self.assertEqual(r.system, a1.system)
        self.assertEqual(r.system, m)
        self.assertEqual(m, a2.system)
        self.assertEqual(len(m.residues), 1)
        self.assertEqual(len(m.atoms), 2)
        self.assertEqual(len(r.atoms), 2)
        r.name='alA'
        r.resid=32
        self.assertEqual(r.name, 'alA')
        self.assertEqual(r.resid, 32)
        
        r.remove()
        r.remove()
        r.remove()
        self.assertEqual(len(m.residues), 0)
        self.assertEqual(len(m.atoms), 0)
        self.assertEqual(len(r.atoms), 0)

    def testSegid(self):
        m=msys.CreateSystem()
        with self.assertRaises(RuntimeError):
            m.addAtomProp('segid', str)
        r=m.addResidue()
        a1=r.addAtom()
        a2=r.addAtom()
        r.chain.segid="WAT1"
        msys.SaveDMS(m,'foo.dms')
        m2=msys.LoadDMS('foo.dms')
        self.assertEqual(1,m.nresidues)
        self.assertEqual(1,m2.nresidues)

    def testChain(self):
        m=msys.CreateSystem()
        c=m.addChain()
        r1=c.addResidue()
        r2=c.addResidue()
        a1=r1.addAtom()
        a2=r2.addAtom()
        self.assertEqual(c.system, r1.system)
        self.assertEqual(c.system, m)
        self.assertEqual(m, r2.system)
        self.assertEqual(len(m.chains), 1)
        self.assertEqual(len(m.residues), 2)
        self.assertEqual(len(c.residues), 2)
        self.assertEqual(len(m.atoms), 2)
        c.remove()
        self.assertEqual(len(m.residues), 0)
        self.assertEqual(len(c.residues), 0)
        self.assertEqual(len(m.atoms), 0)

    def testTermTable(self):
        m=msys.CreateSystem()
        a1=m.addAtom()
        a2=m.addAtom()
        a3=m.addAtom()
        a4=m.addAtom()
        angle=m.addTable("angle", 3)
        self.assertEqual(angle.natoms, 3)
        self.assertEqual(len(angle.terms), 0)
        t1=angle.addTerm(m.atoms[:3])
        self.assertEqual(t1.atoms, m.atoms[:3])
        self.assertTrue(t1.param is None)
        t2=angle.addTerm(m.atoms[1:4], None)
        self.assertTrue(t2.param is None)
        self.assertEqual(len(angle.terms), 2)

        angle.name = 'angle2'
        self.assertEqual(angle.name, 'angle2')
        self.assertTrue('angle2' in m.table_names)
        self.assertFalse('angle' in m.table_names)
        angle.name = 'angle'
        self.assertEqual(angle.name, 'angle')
        self.assertTrue('angle' in m.table_names)
        self.assertFalse('angle2' in m.table_names)

        params=angle.params
        self.assertEqual(params, angle.params)
        p0=params.addParam()
        p1=params.addParam()
        self.assertEqual(p1.table, params)
        self.assertEqual(p0, params.param(0))
        self.assertEqual(p1, params.param(1))
        self.assertEqual(params.nparams, 2)
        t1.param=p1
        self.assertEqual(t1.param, p1)
        t1.param=None
        self.assertEqual(t1.param, None)

        with self.assertRaises(RuntimeError):
            angle.addTerm((m.atom(2),))
        with self.assertRaises(RuntimeError):
            angle.addTerm((m.atom(1),m.atom(1), m.atom(5)))

        angle.remove()
        self.assertFalse('angle' in m.table_names)
        self.assertFalse(angle in m.tables)

    def testDelTerm(self):
        m=msys.CreateSystem()
        a1=m.addAtom()
        a2=m.addAtom()
        a3=m.addAtom()
        a4=m.addAtom()
        table=m.addTable("foo", 2)
        table.addTerm((a1,a2))
        table.addTerm((a1,a3))
        table.addTerm((a1,a4))
        table.addTerm((a2,a3))
        table.addTerm((a4,a2))
        table.addTerm((a4,a3))
        self.assertEqual(table.nterms, 6)
        table.term(2).remove()     # removes term 2
        self.assertEqual(table.nterms, 5)

        table.delTermsWithAtom(a3)  # removes term 1,3,5
        self.assertEqual(table.nterms, 2)
        a4.remove()
        self.assertEqual(table.nterms, 1)


    def testParamProps(self):
        params=msys.CreateParamTable()
        self.assertEqual(len(params.props), 0)
        for n,t in zip(('F', 'I', 'S'), (float, int, str)):
            params.addProp(n,t)
            self.assertTrue(n in params.props)
            self.assertEqual(params.propType(n), t)
        self.assertEqual(params.props, ['F', 'I', 'S'])

        params.delProp('I')
        self.assertEqual(params.props, ['F', 'S'])

        p1=params.addParam()
        p1['F']=1.5
        p2=p1.duplicate()
        self.assertEqual(p1['F'], p2['F'])
        p2['F']=2.5
        self.assertNotEqual(p1['F'], p2['F'])


    def testDirectParamProps(self):
        ''' just like testParamProps, but operate directly on the TermTable
        instead of its ParamTable '''
        m=msys.CreateSystem()
        table=m.addTable("table", 5)
        self.assertEqual(len(table.term_props), 0)
        for n,t in zip(('F', 'I', 'S'), (float, int, str)):
            table.addTermProp(n,t)
            self.assertTrue(n in table.term_props)
            self.assertEqual(table.termPropType(n), t)

    def testPropOverlap(self):
        ''' ensure term props cannot overlap param props. '''
        m=msys.CreateSystem()
        table=m.addTable("table", 1)
        table.params.addProp("a", float)
        with self.assertRaises(RuntimeError):
            table.addTermProp("a", int)


    def testParamWithNoProps(self):
        m=msys.CreateSystem()
        a=m.addAtom()
        table=m.addTable("foo", 1)
        p=table.params.addParam()
        table.addTerm([a], p)
        table.category='bond'
        self.assertEqual(table.category, 'bond')
        msys.SaveDMS(m, 'foo.dms')

    def testFunnyNames(self):
        m=msys.CreateSystem()
        aux=msys.CreateParamTable()
        aux.addProp('group', float)
        aux.addParam()
        m.addAuxTable('aux', aux)
        msys.SaveDMS(m, 'foo.dms')

        m2=m.clone()
        aux2=m2.auxtable('aux')
        self.assertEqual(aux.nprops, aux2.nprops)
        self.assertEqual(aux.nparams, aux2.nparams)

        m3=msys.CreateSystem()
        m3.append(m)
        aux3=m3.auxtable('aux')
        self.assertEqual(aux.nprops, aux3.nprops)
        self.assertEqual(aux.nparams, aux3.nparams)


        table=m.addTable('foo', 1)
        table.category='bond'
        table.addTermProp('select', int)
        table.params.addProp('group', float)
        m.addAtom()
        table.addTerm(m.atoms, table.params.addParam())
        msys.SaveDMS(m, 'bar.dms')

    def testFormalCharge(self):
        m=msys.CreateSystem()
        a=m.addAtom()
        self.assertEqual(a.formal_charge, 0)
        a.formal_charge=32
        self.assertEqual(a.formal_charge, 32)
        a.formal_charge=-10
        self.assertEqual(a.formal_charge, -10)
        msys.SaveDMS(m, 'bar.dms')
        m2=msys.LoadDMS('bar.dms')
        self.assertEqual(m.atom(0).formal_charge, -10)
                
    def testRefcount(self):
        m=msys.CreateSystem()
        a=m.addAtom()
        table=m.addTable("foo", 1)
        ptr=table._ptr
        p1=table.params.addParam()
        p2=table.params.addParam()
        p3=table.params.addParam()
        t1=table.addTerm([a], p1)
        self.assertEqual(ptr.paramRefs(t1.param.id), 1)
        t2=table.addTerm([a], p1)
        self.assertEqual(ptr.paramRefs(t1.param.id), 2)
        self.assertEqual(ptr.paramRefs(t2.param.id), 2)
        t1.remove()
        self.assertEqual(ptr.paramRefs(t2.param.id), 1)
        t3=table.addTerm([a], p2)
        self.assertEqual(ptr.paramRefs(t2.param.id), 1)
        self.assertEqual(ptr.paramRefs(t3.param.id), 1)

        t3.paramB = p2
        self.assertEqual(ptr.paramRefs(t3.param.id), 2)
        self.assertEqual(ptr.paramRefs(t3.paramB.id), 2)

        t2.param=t3.paramB
        self.assertEqual(ptr.paramRefs(t2.param.id), 3)
        self.assertEqual(ptr.paramRefs(t3.param.id), 3)
        self.assertEqual(ptr.paramRefs(t3.paramB.id), 3)

        t3.remove()
        self.assertEqual(ptr.paramRefs(t2.param.id), 1)


    def testSharedParams(self):
        m1=msys.CreateSystem()
        m2=msys.CreateSystem()
        m1.addAtom()
        m2.addAtom()
        m2.addAtom()
        params=msys.CreateParamTable()
        p1=params.addParam()
        p2=params.addParam()
        table1=m1.addTable("table", 1, params)
        self.assertFalse(params.shared)
        table2=m2.addTable("table", 1, params)
        self.assertTrue(params._ptr.shared())
        self.assertEqual(table1.params, table2.params)
        t1=table1.addTerm(m1.atoms, p2)
        t2=table2.addTerm(m2.atoms[1:], p2)
        self.assertEqual(t1.param, t2.param)
        self.assertEqual(t2.param, p2)

        params.addProp("fc", float)
        p1['fc']=32
        p2['fc']=42
        self.assertEqual(t1.param['fc'],42)
        self.assertEqual(t2.param['fc'],42)

        t1['fc']=52
        self.assertEqual(t2['fc'], 52)

    def testTermParamProps(self):
        m=msys.CreateSystem()
        m.addAtom()
        table=m.addTable("table", 1)
        p=table.params.addParam()
        t=table.addTerm(m.atoms, p)
        t2=table.addTerm(m.atoms, p)

        with self.assertRaises(KeyError):
            t['x']
            t.stateB['x']
            t.stateA['x']

        table.params.addProp('x', float)
        table.params.addProp('y', str)
        self.assertEqual(t['x'], 0)
        self.assertEqual(t['y'], '')

        t2['x']=32
        t2['y']='whodat'
        self.assertEqual(t['x'], 0)
        self.assertEqual(t['y'], '')
        self.assertEqual(table.params.nparams, 2)

        self.assertEqual(t2._ptr.getProp(t2.id, 0), 32)
        t2._ptr.setProp(t2.id, 0, 33)
        self.assertEqual(t2._ptr.getProp(t2.id, 0), 33)
        t2._ptr.setProp(t2.id, 0, 32)

        # alchemical term
        b=t2.stateB
        with self.assertRaises(RuntimeError):
            b['x']
        with self.assertRaises(RuntimeError):
            b['y']
        with self.assertRaises(RuntimeError):
            b['x']=42
        
        t2.paramB=t2.param
        self.assertEqual(b.param, t2.paramB)
        self.assertEqual(b['x'], 32)
        self.assertEqual(b['y'], 'whodat')

        self.assertEqual(b._ptr.getPropB(b.id, 0), 32)
        b._ptr.setPropB(b.id, 0, 33)
        self.assertEqual(b._ptr.getPropB(b.id, 0), 33)
        b._ptr.setPropB(b.id, 0, 32)

        self.assertFalse(t2.stateA == t2.stateB)
        self.assertTrue(t2.stateA == t2.stateA)
        self.assertEqual(t2, t2.stateA)



    def testTermProps(self):
        m=msys.CreateSystem()
        m.addAtom()
        table=m.addTable("table", 1)
        F="F"
        I="I"
        table.addTermProp(F, float)
        t1=table.addTerm(m.atoms)
        table.addTermProp(I, int)
        t2=table.addTerm(m.atoms)
        self.assertEqual(t1[F], 0)
        self.assertEqual(t1[I], 0)
        self.assertEqual(t2[F], 0)
        self.assertEqual(t2[I], 0)
        t1[F]=3.5
        t2[I]=42
        self.assertEqual(t1[F], 3.5)
        self.assertEqual(t1[I], 0)
        self.assertEqual(t2[F], 0)
        self.assertEqual(t2[I], 42)
        self.assertEqual(table.term_props, [F, I])

        m2=msys.CreateSystem()
        m2.addAtom()
        with self.assertRaises(RuntimeError):
            table.addTerm(m2.atoms)
        alist=m.atoms
        alist[0]=m2.atoms[0]
        with self.assertRaises(RuntimeError):
            table.addTerm(alist)
        alist[0]=m.atoms[0]
        table.addTerm(alist)

        table.delTermProp(I)
        with self.assertRaises(KeyError):
            t1[I]

    def testAux(self):
        m=msys.CreateSystem()
        e=msys.CreateParamTable()
        m.addAuxTable("cmap", e)
        self.assertTrue('cmap' in m.auxtable_names)
        self.assertEqual(e, m.auxtable('cmap'))
        self.assertTrue(e in m.auxtables)
        m.delAuxTable('cmap')
        self.assertFalse('cmap' in m.auxtable_names)
        self.assertFalse(e in m.auxtables)

    def testTableDMS(self):
        assert 'stretch_harm' in msys.TableSchemas()
        assert 'vdw_12_6' in msys.NonbondedSchemas()

        m=msys.CreateSystem()
        t=m.addTableFromSchema('stretch_harm')
        self.assertEqual(t.natoms, 2)
        self.assertEqual(t.params.props, ['r0', 'fc'])
        self.assertEqual([t.params.propType(n) for n in t.params.props], 
                [float, float])
        self.assertEqual(t.term_props, ['constrained'])
        self.assertEqual(t.termPropType('constrained'), int)

    def testNonbondedDMS(self):
        m=msys.CreateSystem()
        nb=m.addNonbondedFromSchema("vdw_12_6", "arithemetic/geometric")
        nb2=m.addNonbondedFromSchema("vdw_12_6", "arithemetic/geometric")
        m.addNonbondedFromSchema("vdw_12_6")
        self.assertEqual(nb,nb2)
        params=nb.params
        props=params.props
        self.assertEqual(props, ['sigma', 'epsilon'])
        self.assertEqual([nb.params.propType(n) for n in props], [float,float])

    def testGlobalCell(self):
        m=msys.CreateSystem()
        m.cell.A.x=32
        self.assertEqual(m.cell.A.x, 32)
        tgt=[1,2,3]
        m.cell.A[:]=tgt
        m.cell[1][:]=tgt
        self.assertEqual(m.cell.A, m.cell.B)
        self.assertNotEqual(m.cell.A, m.cell.C)
        with self.assertRaises(IndexError): m.cell[3]
        with self.assertRaises(IndexError): m.cell[-4]

    def testNonbondedInfo(self):
        m=msys.CreateSystem()
        nb=m.nonbonded_info
        nb.vdw_funct = "justinrocks"
        nb.vdw_rule = "yep"
        self.assertEqual(nb.vdw_funct , "justinrocks")
        self.assertEqual(nb.vdw_rule , "yep")

    def testClone(self):
        m=msys.CreateSystem()
        m.addAtom().name='a'
        m.addAtom().name='b'
        m.addAtom().name='c'
        b1=m.atom(0).addBond(m.atom(1))
        with self.assertRaises(KeyError):
            b1['res_order']=3.5
        m.addBondProp('res_order', float)
        b1['res_order']=3.5

        c=msys.CloneSystem(m.atoms[::-1])
        self.assertEqual( [a.name for a in c.atoms], ['c', 'b', 'a'])
        self.assertEqual(c.bond(0)['res_order'], 3.5)

        with self.assertRaises(RuntimeError):
            msys.CloneSystem([m.atoms[0], m.atoms[1], m.atoms[0]])

        m.atom(2).remove()
        with self.assertRaises(RuntimeError):
            msys.CloneSystem([m.atom(0), m.atom(1), m.atom(2)])

    def testAppend(self):
        m=msys.CreateSystem()
        a0=m.addAtom()
        a0.name='a'
        a1=m.addAtom()
        a1.name='b'
        b=a0.addBond(a1)
        m.addAtomProp('foo', float)
        m.addBondProp('bar', int)
        a1['foo']=3.14
        b['bar']=42
        m.append(m)
        self.assertEqual( [a.name for a in m.atoms], ['a', 'b', 'a', 'b'])
        self.assertEqual( m.atom(2)['foo'], 0 )
        self.assertEqual( m.atom(3)['foo'], 3.14 )
        self.assertEqual( m.bond(1)['bar'], 42)

    def testUpdateFragids(self):
        m=msys.CreateSystem()
        a1=m.addAtom()
        a2=m.addAtom()
        a3=m.addAtom()
        def fragids(m): return [a.fragid for a in m.atoms]

        frags=m.updateFragids()
        self.assertEqual(fragids(m), [0,1,2])
        self.assertEqual(frags, [[m.atom(i)] for i in range(3)])

        a1.addBond(a3)
        frags=m.updateFragids()
        self.assertEqual(fragids(m), [0,1,0])
        self.assertEqual(frags, [[m.atom(0), m.atom(2)], [m.atom(1)]])

    def testBadDMS(self):
        path='/tmp/_tmp_.dms'
        m=msys.CreateSystem()
        msys.SaveDMS(m, path)
        a0=m.addAtom()
        msys.SaveDMS(m, path)
        nb=m.addNonbondedFromSchema('vdw_12_6', 'geometric')
        # can't save - no terms for particle 0
        with self.assertRaises(RuntimeError):
            msys.SaveDMS(m, path)
        t=nb.addTerm([a0])
        # can't save - no param
        with self.assertRaises(RuntimeError):
            msys.SaveDMS(m, path)
        p0=nb.params.addParam()
        t.param=p0
        # now we can save
        msys.SaveDMS(m, path)
        # twiddle param to something bad
        t._ptr.setParam(t.id, 42)
        with self.assertRaises(RuntimeError):
            msys.SaveDMS(m, path)
        t._ptr.setParam(t.id, 0)

        stretch=m.addTableFromSchema('stretch_harm')
        t=stretch.addTerm([a0,a0])
        with self.assertRaises(RuntimeError):
            msys.SaveDMS(m, path)
        p=stretch.params.addParam()
        t.param=p
        msys.SaveDMS(m, path)
        t._ptr.setParam(t.id, 42)
        with self.assertRaises(RuntimeError):
            msys.SaveDMS(m, path)
        t.param=p
        t.paramB=p
        msys.SaveDMS(m, path)
        with self.assertRaises(RuntimeError):
            t._ptr.setParamB(t.id, 42)

    def testPositions(self):
        m=msys.CreateSystem()
        a0=m.addAtom()
        a1=m.addAtom()
        a2=m.addAtom()
        a0.y=1
        a1.z=2
        a2.x=3
        p=m.positions
        self.assertEqual(p[0][1],1)
        self.assertEqual(p[1][2],2)
        self.assertEqual(p[2][0],3)
        p[1][2]=4
        m.positions=p
        p=m.positions
        self.assertEqual(p[1][2],4)
        self.assertEqual(p, m.positions)
        del p[2]
        with self.assertRaises(ValueError):
            m.positions=p
        del p[0][2]
        with self.assertRaises(ValueError):
            m.positions=p

    def testMacros(self):
        m=msys.CreateSystem()
        m.addAtom().name='CA'
        m.addAtom().name='CB'
        self.assertFalse('foobar' in m.selection_macros)
        with self.assertRaises(RuntimeError): m.select('foobar')
        m.addSelectionMacro('foobar', 'name CB')
        self.assertEqual(m.selectionMacroDefinition('foobar'), 'name CB')
        self.assertTrue('foobar' in m.selection_macros)
        self.assertEqual(m.select('foobar')[0].id, 1)

        m2=m.clone()
        self.assertEqual(m2.select('foobar')[0].id, 1)

        m.delSelectionMacro('foobar')
        with self.assertRaises(RuntimeError): m.select('foobar')

        m.addSelectionMacro('foo', 'name CA')
        m.addSelectionMacro('bar', 'foo')
        m.addSelectionMacro('foo', 'bar')
        with self.assertRaises(RuntimeError):
            m.select('foo')


if __name__=="__main__":
    unittest.main()
