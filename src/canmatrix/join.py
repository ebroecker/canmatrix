import canmatrix.formats
from canmatrix.canmatrix import CanId


def list_pgn(db):
    """

    :param db:
    :return: pgn and id
    """
    msg_id = [x.id for x in db.frames]
    r = [CanId(t).tuples() for t in msg_id]
    return [t[1] for t in r], msg_id


def ids_sharing_same_pgn(id_x, pgn_x, id_y, pgn_y):
    for idx, pgnx in zip(id_x, pgn_x):
        for idy, pgny in zip(id_y, pgn_y):
            if pgnx == pgny:
                yield (idx, idy)


def join_frame_by_signal_startbit(files):
    target_db = next(iter(canmatrix.formats.loadp(files.pop(0)).values()))

    pgn_x, id_x = list_pgn(db=target_db)

    for f in files:
        source_db = next(iter(canmatrix.formats.loadp(f).values()))
        pgn_y, id_y = list_pgn(db=source_db)

        same_pgn = ids_sharing_same_pgn(id_x, pgn_x, id_y, pgn_y)

        for idx, idy in same_pgn:
            # print("{0:#x} {1:#x}".format(idx, idy))
            target_fr = target_db.frame_by_id(idx)
            source_fr = source_db.frame_by_id(idy)

            to_add = []
            for sig_t in target_fr.signals:
                for sig_s in source_fr.signals:
                    # print(sig.name)
                    if sig_t.startbit == sig_s.startbit:
                        # print("\t{0} {1}".format(sig_t.name, sig_s.name))
                        to_add.append(sig_s)
            for s in to_add:
                target_fr.add_signal(s)

    return target_db


def rename_frame_with_id(source_db):
    for frameSc in source_db.frames:
        _, pgn, sa = CanId(frameSc.id).tuples()

        exten = "__{pgn:#04X}_{sa:#02X}_{sa:03d}d".format(pgn=pgn, sa=sa)
        new_name = frameSc.name + exten
        # print(new_name)
        frameSc.name = new_name


def rename_frame_with_sae_acronym(source_db, target_db):
    pgn_x, id_x = list_pgn(db=target_db)
    pgn_y, id_y = list_pgn(db=source_db)
    same_pgn = ids_sharing_same_pgn(id_x, pgn_x, id_y, pgn_y)

    for idx, idy in same_pgn:
        target_fr = target_db.frame_by_id(idx)
        source_fr = source_db.frame_by_id(idy)

        new_name = source_fr.name + "__" + target_fr.name
        target_fr.name = new_name


def join_frame_for_manufacturer(db, files):
    # target_db = next(iter(im.importany(files.pop(0)).values()))

    pgn_x, id_x = list_pgn(db=db)

    for f in files:
        source_db = next(iter(canmatrix.formats.loadp(f).values()))
        pgn_y, id_y = list_pgn(db=source_db)

        same_pgn = ids_sharing_same_pgn(id_x, pgn_x, id_y, pgn_y)

        for idx, idy in same_pgn:
            # print("{0:#x} {1:#x}".format(idx, idy))
            target_fr = db.frame_by_id(idx)
            source_fr = source_db.frame_by_id(idy)

            _, pgn, sa = CanId(target_fr.id).tuples()
            if sa < 128:
                print('less', target_fr.name)
                to_add = []
                for sig_s in source_fr.signals:
                    new_name = "{name}_{pgn:#04x}_{sa:03}".format(
                        name=sig_s.name, pgn=pgn, sa=sa)
                    sig_s.name = new_name
                    to_add.append(sig_s)
                for s in to_add:
                    target_fr.add_signal(s)
