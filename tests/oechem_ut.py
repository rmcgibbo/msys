#!/usr/bin/garden-exec
#{
# garden env-keep-only TMPDIR
# source `dirname $0`/../MODULES
# garden load $PYTHON/bin
# if [ "$1" == "-3" ]
# then
#    shift
#    garden load desres-python/3.6.1-01c7/bin
#    PY=python3
# else
#    PY=python
# fi
# garden load openeye-toolkits/2017.6.1-01c7/lib-$PY
# exec $PY $0 "$@"
#}

from __future__ import print_function

import os, sys
TMPDIR = os.getenv('TMPDIR', 'objs/%s/x86_64' % os.getenv('DESRES_OS'))
suffix = '3' if sys.version_info.major==3 else ''
sys.path.insert(0, os.path.join(TMPDIR, 'lib', 'python%s' % suffix))
import msys
import numpy as np

import unittest
from openeye import oechem
from time import time

class Main(unittest.TestCase):
    def testSmall(self):
        mol = msys.Load('tests/files/jandor-bad.sdf')
        
        # by default ConvertToOEChem doesn't assign the formal charges, should it?!
        contains_radicals = "C[C@H]([C@@H]1[C@H]2[C@H](C(=C(N2C1=O)C(=O)OCc3ccc(cc3)[N](=O)[O])Sc4ncccn4)OC)O"
        oemol = msys.ConvertToOEChem(mol)
        self.assertEqual(oechem.OEMolToSmiles(oemol), contains_radicals)

        # Using OEChem to assign the formal charges
        properly_charged = "C[C@H]([C@@H]1[C@H]2[C@H](C(=C(N2C1=O)C(=O)OCc3ccc(cc3)[N+](=O)[O-])Sc4ncccn4)OC)O"
        oechem.OEAssignFormalCharges(oemol)
        self.assertEqual(oechem.OEMolToSmiles(oemol), properly_charged)

        # using msys to assign formal charges
        msys.AssignBondOrderAndFormalCharge(mol)
        amol = msys.AnnotatedSystem(mol)
        oemol = msys.ConvertToOEChem(mol)
        self.assertEqual(oechem.OEMolToSmiles(oemol), properly_charged)
        for matm, ratm in zip(mol.atoms, oemol.GetAtoms()):
            self.assertEqual(matm.atomic_number, ratm.GetAtomicNum())
            self.assertEqual(matm.formal_charge, ratm.GetFormalCharge())
            self.assertEqual(amol.valence(matm), ratm.GetExplicitValence())

    def testBig(self):
        mol = msys.Load('tests/files/2f4k.dms')
        msys.AssignBondOrderAndFormalCharge(mol)
        t = -time()
        oemol = msys.ConvertToOEChem(mol)
        t += time()
        print("%s: %d atoms, %d bonds in %.3fs" % (mol.name, mol.natoms, mol.nbonds, t))

    def checkStereo(self, atom, expected):
        self.assertTrue(atom.IsChiral())
        self.assertTrue(atom.HasStereoSpecified())
        
        v = []
        for nbr in atom.GetAtoms():
            v.append(nbr)
        stereo = atom.GetStereo(v, oechem.OEAtomStereo_Tetrahedral)
        self.assertEqual(stereo, expected)

    def testChiralAtoms(self):
        mol = msys.Load('tests/files/jandor.sdf')
        oemol = msys.ConvertToOEChem(mol)
        for r in oemol.GetAtoms():
            if r.GetIdx() in (0,4,7):
                self.checkStereo(r, oechem.OEAtomStereo_RightHanded)
            elif r.GetIdx() in (5,):
                self.checkStereo(r, oechem.OEAtomStereo_LeftHanded)

    def checkBondStereo(self, bond, expected):
        v = []
        for neigh in bond.GetBgn().GetAtoms():
            if neigh != bond.GetEnd():
                v.append(neigh)
                break
        for neigh in bond.GetEnd().GetAtoms():
            if neigh != bond.GetBgn():
                v.append(neigh)
                break
        stereo = bond.GetStereo(v, oechem.OEBondStereo_CisTrans)
        self.assertEqual(stereo, expected)

    def testBondStereo(self):
        sdf = 'tests/files/34106.sdf'
        mol = msys.Load(sdf)
        oemol = msys.ConvertToOEChem(mol)
        for bond in oemol.GetBonds():
            ai = bond.GetBgnIdx()
            aj = bond.GetEndIdx()
            if ai == 16 and aj == 17:
                self.assertTrue(bond.HasStereoSpecified(oechem.OEBondStereo_CisTrans))
                self.checkBondStereo(bond, oechem.OEBondStereo_Cis)
            else:
                self.assertFalse(bond.HasStereoSpecified(oechem.OEBondStereo_CisTrans))
                self.checkBondStereo(bond, oechem.OEBondStereo_Undefined)

    def testOmega(self):
        sdf = 'tests/files/methotrexate.sdf'
        mol = msys.Load(sdf)
        dms = 'methotrexate.dms'
        msys.Save(mol, dms)
        mol = msys.Load(dms)

        oemol = msys.ConvertToOEChem(mol)

        from openeye import oeomega
        opts = oeomega.OEOmegaOptions()
        opts.SetMaxConfs(1)
        opts.SetStrictStereo(False)
        omega = oeomega.OEOmega(opts)

        # OEOmegaOptions.SetCanonOrder canonicalizes the order of the
        # atoms in the molecule in order to make conformer generation
        # invariant of input atom order.
        for orig_idx, atom in enumerate(oemol.GetAtoms()):
            atom.SetData("orig_idx", orig_idx)
        assert omega(oemol)
        orig_idx_to_new_idx = {}
        for atom in oemol.GetAtoms():
            orig_idx_to_new_idx[atom.GetData("orig_idx")] = atom.GetIdx()

        for conf in oemol.GetConfs():
            coords = conf.GetCoords()
            npcrds = np.array([coords[orig_idx_to_new_idx[orig_idx]] for orig_idx in sorted(orig_idx_to_new_idx)])
            break

        cmol = mol.clone()
        cmol.positions = npcrds

        avg_length = 0.0
        for bond in cmol.bonds:
            vec = bond.first.pos - bond.second.pos
            avg_length += np.sqrt(vec.dot(vec))
        avg_length /= cmol.nbonds
        assert avg_length < 2.5, "average bond length is %.2f, atom order is likely screwed up!" % avg_length

        #msys.Save(cmol, 'meth_confs.sdf')

if __name__=="__main__":
  unittest.main(verbosity=2)