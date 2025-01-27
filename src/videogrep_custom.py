import videogrep
import random
import os
import subprocess
from typing import List, Union

BATCH_SIZE = 20
SUB_EXTS = [".json", ".vtt", ".srt", ".transcript"]

SEARCH_ORDERD = "ordered"


def search_custom_order(inputfile, custom_order):
    print("custom_order %s" % custom_order)
    clips = []
    for phrase in custom_order:
        matches = videogrep.search(inputfile, phrase, search_type="fragment")
        if matches:
            clips.append(matches[0])

    return clips


def pad_and_sync_ordered(
    segments: List[dict], padding: float = 0, resync: float = 0
) -> List[dict]:
    """
    Adds padding and resyncs

    :param segments List[dict]: Segments
    :param padding float: Time in seconds to pad each clip
    :param resync float: Time in seconds to shift subtitle timestamps
    :rtype List[dict]: Padded and cleaned output
    """

    if len(segments) == 0:
        return []

    for s in segments:
        if padding != 0:
            s["start"] -= padding
            s["end"] += padding
        if resync != 0:
            s["start"] += resync
            s["end"] += resync

        if s["start"] < 0:
            s["start"] = 0
        if s["end"] < 0:
            s["end"] = 0

    out = [segments[0]]
    for segment in segments[1:]:
        prev_file = out[-1]["file"]
        current_file = segment["file"]
        if current_file != prev_file:
            out.append(segment)
            continue

        out.append(segment)

    return out


def videogrep_custom(
    files: Union[List[str], str],
    query: Union[List[str], str],
    search_type: str = "sentence",
    output: str = "supercut.mp4",
    resync: float = 0,
    padding: float = 0,
    maxclips: int = 0,
    export_clips: bool = False,
    random_order: bool = False,
    demo: bool = False,
    write_vtt: bool = False,
    preview: bool = False,
):
    """
    Creates a supercut of videos based on a search query

    :param files List[str]: Video file to search through
    :param query str: A query, as a regular expression
    :param search_type str: Either 'sentence', 'ordered' or 'fragment'
    :param output str: Filename to save to
    :param resync float: Time in seconds to shift subtitle timestamps
    :param padding float: Time in seconds to pad each clip
    :param maxclips int: Maximum clips to use (0 is unlimited)
    :param export_clips bool: Export individual clips rather than a single file (default False)
    :param random_order bool: Randomize the order of clips (default False)
    :param demo bool: Show the results of the search but don't actually make a supercut
    :param write_vtt bool: Write a WebVTT file next to the supercut (default False)
    """

    segments = []
    splits = []
    for s in query:
        splits.extend(s.split(";"))

    if search_type == SEARCH_ORDERD:
        segments = search_custom_order(files, splits)
    else:
        segments = videogrep.search(files, splits, search_type)

    print("Segements before: ", segments.__len__())

    if len(segments) == 0:
        if isinstance(query, list):
            query = " ".join(query)
        print("No results found for", query)
        return False

    # padding
    if search_type == SEARCH_ORDERD:
        segments = pad_and_sync_ordered(segments, padding=padding, resync=resync)
    else:
        segments = videogrep.pad_and_sync(segments, padding=padding, resync=resync)

    print("Segements after: ", segments.__len__())

    # random order
    if random_order and search_type != SEARCH_ORDERD:
        random.shuffle(segments)

    # max clips
    if maxclips != 0:
        segments = segments[0:maxclips]

    # demo and exit
    if demo:
        for s in segments:
            print(s["file"], s["start"], s["end"], s["content"])
        return True

    # preview in mpv and exit
    if preview:
        lines = [f"{s['file']},{s['start']},{s['end']-s['start']}" for s in segments]
        edl = "edl://" + ";".join(lines)
        subprocess.run(["mpv", edl])
        return True

    # export individual clips
    if export_clips:
        videogrep.export_individual_clips(segments, output)
        return True

    # m3u
    if output.endswith(".m3u"):
        videogrep.export_m3u(segments, output)
        return True

    # mpv edls
    if output.endswith(".mpv.edl"):
        videogrep.export_mpv_edl(segments, output)
        return True

    # fcp xml (compatible with premiere/davinci)
    if output.endswith(".xml"):
        videogrep.export_xml(segments, output)
        return True

    # export supercut
    if len(segments) > BATCH_SIZE:
        videogrep.create_supercut_in_batches(segments, output)
    else:
        videogrep.create_supercut(segments, output)

    # write WebVTT file
    if write_vtt:
        basename, ext = os.path.splitext(output)
        videogrep.vtt.render(segments, basename + ".vtt")
