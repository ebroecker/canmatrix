# -*- coding: utf-8 -*-

import typing

import canmatrix
import canmatrix.formats


def list_pgn(db):
    # type: (canmatrix.CanMatrix) -> typing.Tuple[typing.List[int], typing.List[canmatrix.ArbitrationId]]
    """
    Get all PGN values for given frame.

    :param db: CanMatrix database
    :return: tuple of [pgn] and [arbitration_id]
    """
    id_list = [x.arbitration_id for x in db.frames]
    pgn_list = [arb_id.pgn for arb_id in id_list]
    return pgn_list, id_list


def ids_sharing_same_pgn(id_x, pgn_x, id_y, pgn_y):
    # type: (typing.Sequence[canmatrix.ArbitrationId], typing.Sequence[int], typing.Sequence[canmatrix.ArbitrationId], typing.Sequence[int]) -> typing.Iterable[typing.Tuple[canmatrix.ArbitrationId, canmatrix.ArbitrationId]]
    """Yield arbitration ids which has the same pgn."""
    for id_a, pgn_a in zip(id_x, pgn_x):
        for id_b, pgn_b in zip(id_y, pgn_y):
            if pgn_a == pgn_b:
                yield (id_a, id_b)


def join_frame_by_signal_start_bit(files):  # type: (typing.List[str]) -> canmatrix.CanMatrix
    target_db = next(iter(canmatrix.formats.loadp(files.pop(0)).values()))  # type: canmatrix.CanMatrix

    pgn_x, id_x = list_pgn(db=target_db)

    for f in files:
        source_db = next(iter(canmatrix.formats.loadp(f).values()))  # type: canmatrix.CanMatrix
        pgn_y, id_y = list_pgn(db=source_db)

        same_pgn = ids_sharing_same_pgn(id_x, pgn_x, id_y, pgn_y)

        for id_a, id_b in same_pgn:
            # print("{0:#x} {1:#x}".format(id_x, id_y))
            target_fr = target_db.frame_by_id(id_a)
            source_fr = source_db.frame_by_id(id_b)

            signal_to_add = []  # type: typing.List[canmatrix.Signal]
            for sig_t in target_fr.signals:
                for sig_s in source_fr.signals:
                    # print(sig.name)
                    if sig_t.start_bit == sig_s.start_bit:
                        # print("\t{0} {1}".format(sig_t.name, sig_s.name))
                        signal_to_add.append(sig_s)
            for s in signal_to_add:
                target_fr.add_signal(s)
    return target_db


def rename_frame_with_id(source_db):  # type: (canmatrix.CanMatrix) -> None
    for frameSc in source_db.frames:
        _, pgn, sa = frameSc.arbitration_id.j1939_tuple()

        extension = "__{pgn:#04X}_{sa:#02X}_{sa:03d}d".format(pgn=pgn, sa=sa)
        new_name = frameSc.name + extension
        # print(new_name)
        frameSc.name = new_name


def rename_frame_with_sae_acronym(source_db, target_db):  # type: (canmatrix.CanMatrix, canmatrix.CanMatrix) -> None
    pgn_x, id_x = list_pgn(db=target_db)
    pgn_y, id_y = list_pgn(db=source_db)
    same_pgn = ids_sharing_same_pgn(id_x, pgn_x, id_y, pgn_y)

    for idx, idy in same_pgn:
        target_fr = target_db.frame_by_id(idx)
        source_fr = source_db.frame_by_id(idy)

        new_name = source_fr.name + "__" + target_fr.name
        target_fr.name = new_name


def join_frame_for_manufacturer(db, files):  # type: (canmatrix.CanMatrix, typing.Sequence[str]) -> None
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

            _, pgn, sa = target_fr.arbitration_id.j1939_tuple()
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
