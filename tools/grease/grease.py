
import os, msys

def Grease(mol, tile, thickness=0.0, xsize=None, ysize=None,
            chain='LIP', verbose=False, 
            square=False):
    '''
    Build and return a new system consisting of mol plus lipid bilayer.
    Tile is the lipid bilayer system to replicate.

    If no solute is provided, the solute is treated as a point at the
    origin.  thickness specifies the amount of solute added along the x
    and y axis.  The dimensions of the bilayer can also be given explicitly
    with dimensions.  If square is true, the box size will be expanded to
    the size of the longest dimension.

    Return the greased system; no modifications are made to the input system.
    '''

    mol=msys.CloneSystem(mol.atoms)

    lipsize=[tile.cell[i][i] for i in range(3)]

    # find a chain name for the lipids that doesn't overlap with the 
    # input structure.
    chains = set(c.name for c in mol.chains)
    lipchain = 'X'
    while lipchain in chains:
        lipchain += 'X'
    for c in tile.chains:
        c.name = lipchain

    if xsize is None or ysize is None:
        if verbose: print "finding bounding box..."
        if len(mol.atoms):
            first=mol.atoms[0].pos
            xmin, ymin, zmin = first
            xmax, ymax, zmax = first
            for a in mol.atoms:
                x,y,z = a.pos
                if   x<xmin: xmin=x
                elif x>xmax: xmax=x
                if   y<ymin: ymin=y
                elif y>ymax: ymax=y
                if   z<zmin: zmin=z
                elif z>zmax: zmax=z
            if xsize is None: xsize = thickness + xmax - xmin
            if ysize is None: ysize = thickness + ymax - ymin
        else:
            if xsize is None: xsize = thickness
            if xsize is None: ysize = thickness
        
    xsize = float(xsize)
    ysize = float(ysize)

    if square:
        xsize = max(xsize, ysize)
        ysize = xsize

    # extract where to put the lipid
    nx = int(xsize/lipsize[0]) + 1
    ny = int(ysize/lipsize[1]) + 1

    xshift = -0.5 * (nx-1)*lipsize[0]
    yshift = -0.5 * (ny-1)*lipsize[1]
    xmin = -0.5 * xsize
    ymin = -0.5 * ysize
    xmax = -xmin
    ymax = -ymin

    # replicate the template lipid box
    if verbose: print "replicating %d x %d" % (nx,ny)
    for i in range(nx):
        xdelta = xshift + i*lipsize[0]
        for j in range(ny):
            ydelta = yshift + j*lipsize[1]
            newatoms = mol.append(tile)
            for a in newatoms:
                a.x += xdelta
                a.y += ydelta

    if verbose: print "replicated system contains %d atoms" % mol.natoms
    if verbose: print "removing overlap with solute"
    headgroup_dist = 2.0
    mol = msys.CloneSystem(mol.atomselect(
        'not (chain %s and same residue as (atomicnumber 8 15 and pbwithin %f of (noh and not chain %s)))' % (
            lipchain, headgroup_dist, lipchain)))
    dist = 1.0
    mol = msys.CloneSystem(mol.atomselect(
        'not (chain %s and same residue as (pbwithin %f of (noh and not chain %s)))' % (
            lipchain, dist, lipchain)))
    if verbose: print "after removing solute overlap, have %d atoms" % mol.natoms

    if verbose: print "removing outer lipids"
    mol = msys.CloneSystem(mol.atomselect(
        'not (chain %s and same residue as (atomicnumber 15 and (abs(x)>%f or abs(y)>%f)))' % (
            lipchain,xmax,ymax)))
    if verbose: print "after removing outer lipids, have %d atoms" % mol.natoms

    # assign the lipid chain name, and renumber lipid resids
    lipnum = 1
    for c in mol.chains:
        if c.name == lipchain:
            c.name = chain
            for r in c.residues:
                r.num = lipnum
                lipnum += 1

    mol.reassignGids()

    if verbose: print "updating global cell"

    # update the cell
    mol.cell[0][:]=[xsize,0,0]
    mol.cell[1][:]=[0,ysize,0]
    mol.cell[2][:]=[0,0,max(mol.cell[2][2], lipsize[2])]

    return mol

