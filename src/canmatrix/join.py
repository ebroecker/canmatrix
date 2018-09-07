import canmatrix.formats
from canmatrix.canmatrix import CanId


def list_pgn(db):
    """

    :param db:
    :return: pgn and id
    """
    id = [x.id for x in db.frames]
    r = [CanId(t).tuples() for t in id]
    return [t[1] for t in r], id


def ids_sharing_same_pgn(id_x, pgn_x, id_y, pgn_y):
    for idx, pgnx in zip(id_x, pgn_x):
        for idy, pgny in zip(id_y, pgn_y):
            if pgnx == pgny:
                yield (idx, idy)


def join_frame_by_signal_startbit(files):
    targetDb = next(iter(canmatrix.formats.loadp(files.pop(0)).values()))

    pgn_x, id_x = list_pgn(db=targetDb)

    for f in files:
        sourceDb = next(iter(canmatrix.formats.loadp(f).values()))
        pgn_y, id_y = list_pgn(db=sourceDb)

        same_pgn = ids_sharing_same_pgn(id_x, pgn_x, id_y, pgn_y)

        for idx, idy in same_pgn:
            # print("{0:#x} {1:#x}".format(idx, idy))
            targetFr = targetDb.frameById(idx)
            sourceFr = sourceDb.frameById(idy)

            to_add = []
            for sig_t in targetFr.signals:
                for sig_s in sourceFr.signals:
                    # print(sig.name)
                    if sig_t.startbit == sig_s.startbit:
                        # print("\t{0} {1}".format(sig_t.name, sig_s.name))
                        to_add.append(sig_s)
            for s in to_add:
                targetFr.addSignal(s)

    return targetDb


def renameFrameWithID(sourceDb):
    for frameSc in sourceDb.frames:
        _, pgn, sa = CanId(frameSc.id).tuples()

        exten = "__{pgn:#04X}_{sa:#02X}_{sa:03d}d".format(pgn=pgn, sa=sa)
        new_name = frameSc.name + exten
        # print(new_name)
        frameSc.name = new_name


def renameFrameWithSAEacronyme(sourceDb, targetDb):
    pgn_x, id_x = list_pgn(db=targetDb)
    pgn_y, id_y = list_pgn(db=sourceDb)
    same_pgn = ids_sharing_same_pgn(id_x, pgn_x, id_y, pgn_y)

    for idx, idy in same_pgn:
        targetFr = targetDb.frameById(idx)
        sourceFr = sourceDb.frameById(idy)

        new_name = sourceFr.name + "__" + targetFr.name
        targetFr.name = new_name


def join_frame_for_manufacturer(db, files):
    #targetDb = next(iter(im.importany(files.pop(0)).values()))

    pgn_x, id_x = list_pgn(db=db)

    for f in files:
        sourceDb = next(iter(canmatrix.formats.loadp(f).values()))
        pgn_y, id_y = list_pgn(db=sourceDb)

        same_pgn = ids_sharing_same_pgn(id_x, pgn_x, id_y, pgn_y)

        for idx, idy in same_pgn:
            # print("{0:#x} {1:#x}".format(idx, idy))
            targetFr = db.frameById(idx)
            sourceFr = sourceDb.frameById(idy)

            _, pgn, sa = CanId(targetFr.id).tuples()
            if(sa < 128):
                print('less', targetFr.name)
                to_add = []
                for sig_s in sourceFr.signals:
                    new_name = "{name}_{pgn:#04x}_{sa:03}".format(
                        name=sig_s.name, pgn=pgn, sa=sa)
                    sig_s.name = new_name
                    to_add.append(sig_s)
                for s in to_add:
                    targetFr.addSignal(s)
