from collections import Counter
from datetime import datetime, timedelta
from typing import List, NamedTuple

from lxml.etree import _Element

from log_helper.config import delimiters, hundred_episodes_after_60, hundred_episodes_up_to_60
from log_helper.errors import DeltaBaseZero
from log_helper.utils.fcpxml import Clip, Bin
from log_helper.utils.mergeclip import merge

FRAMESPERDAY = 2160000


class WorkArguments(NamedTuple):
    file: str
    bin: bool
    next_day: bool
    prev_day: bool
    rename: bool
    merge: bool
    batch: bool
    testing: bool


class Delta(NamedTuple):
    delta_in: int
    in_frame: int
    base: float
    k_max: int


def calculate_delta(clip_list: List[Clip], arguments: WorkArguments) -> Delta:
    video_in_marked_frame = 0
    video_out_marked_frame = 0
    audio_in_marked_frame = 0
    audio_out_marked_frame = 0
    for clip in clip_list:
        start_frame = clip.get_timecode_frame('source')
        if not start_frame:
            continue
        if clip.in_ != -1:
            marked_frame = int(start_frame) + int(clip.in_)
            clip.in_ = -1
            if clip.is_video():
                video_in_marked_frame = marked_frame
            else:
                audio_in_marked_frame = marked_frame
        if clip.out != -1:
            marked_frame = int(start_frame) + int(clip.out)
            clip.out = -1
            if clip.is_video():
                video_out_marked_frame = marked_frame
            else:
                audio_out_marked_frame = marked_frame
        if arguments.testing:
            print(clip.id_)
            print(video_in_marked_frame)
            print(audio_in_marked_frame)
            print(video_out_marked_frame)
            print(audio_out_marked_frame)

    if video_in_marked_frame == video_out_marked_frame:
        raise DeltaBaseZero
    audio_out_marked_frame += FRAMESPERDAY if audio_out_marked_frame < audio_in_marked_frame else 0
    video_out_marked_frame += FRAMESPERDAY if video_out_marked_frame < video_in_marked_frame else 0

    delta_in = audio_in_marked_frame - video_in_marked_frame
    delta_out = audio_out_marked_frame - video_out_marked_frame
    k_max = delta_out - delta_in

    if arguments.rename:
        print('delta_in  =', delta_in)
        print('delta_out =', delta_out)
        print('k_max     =', k_max)

    # if delta_in <= 0:  # в бине нет аудио
    # if in_frame == 0:  # в бине нет видео. приводит к делению на ноль.
    #                      тк base == 0, а в insert_aux_timecode есть деление на base

    return Delta(delta_in=delta_in, in_frame=video_in_marked_frame,
                 base=float(video_out_marked_frame - video_in_marked_frame), k_max=k_max)


def insert_aux_timecode(clip: Clip, delta: Delta):
    clip.remove_timecode('aux1')

    current_frame = clip.get_timecode_frame('source')
    if not current_frame:
        current_frame = 0

    if not delta.base:
        print(clip.logginginfo)
        raise DeltaBaseZero

    k = (current_frame - delta.in_frame) / delta.base

    frames_with_delta = current_frame + delta.delta_in + round(delta.k_max * k)
    if frames_with_delta > FRAMESPERDAY - 1:
        frames_with_delta = frames_with_delta - FRAMESPERDAY

    clip.insert_timecode(frames_with_delta if clip.is_video() else current_frame, 'aux1', reel_name='001')


def get_log_from_name(name: str) -> tuple:
    if name[-4:].lower() == '-nr2':
        name = name[:-4]
    if name[0] == '+':
        name = name[1:]
    if name[-1].lower() == 'a':
        name = name[:-1]
    name = name.replace('ZK', '_ZK_')
    for delimiter in delimiters:
        name = name.replace(delimiter, '_')
    seq = name.split('_')
    series = seq[0]
    shot = seq[-2]
    take = seq[-1]
    scene = name[len(series) + 1:-1 - len(shot) - 1 - len(take)]
    if not scene:
        scene = '00'

    return series, scene, shot, take


def take_correcting(take: str) -> str:
    pick_up = ''
    if take[-1].lower() == 'p':
        take = take[:-1]
        pick_up = 'pu'
    elif take[-2:].lower() == 'p2':
        take = take[:-2]
        pick_up = 'pu2'
    elif take[-2:].lower() == 'p3':
        take = take[:-2]
        pick_up = 'pu3'
    if len(take) < 2:
        take = '0' + take

    return take + pick_up


def shot_correcting(shot: str) -> str:
    dop = ''
    if shot[-1].lower() == 'd':
        shot = shot[:-1]
        dop = 'dop'
    if len(shot) > 1 and shot[-2].lower() == 'd':
        dop = 'dop' + shot[-1]
        shot = shot[:-2]
    if len(shot) < 2:
        shot = '0' + shot
    if len(shot) > 2 and shot[-3] == '0':
        shot = shot[-2:]

    return shot + dop


def scene_correcting(scene: str) -> str:
    flash_back = ''
    if len(scene.split('-')) > 1:
        scene = scene.replace('-', '+')
    elif len(scene.split('_')) > 1:
        scene = scene.replace('_', '+')
    elif len(scene.split('.')) > 1 and len(scene.split('.')[1]) > 1:
        scene = scene.replace('.', '+')
    scene_list = []
    for item in scene.split('+'):
        # print(f'{item} in {scene}')
        if item[-1].lower() == 'f':
            flash_back = 'FB'
            item = item[:-1]
        if item[-1].lower() == 'b':
            flash_back = 'FB'
            item = item[:-2]
        if len(item) < 2:
            item = '0' + item
        scene_list.append(item + flash_back)

    return '+'.join(scene_list)


def series_correcting(series: str) -> str:
    if len(series) > 4:
        series = series[:4]
    if len(series) < 3:
        if series.isnumeric():
            if int(series) > 60:
                series = hundred_episodes_after_60 + series
            else:
                series = hundred_episodes_up_to_60 + series

    return series


def set_log_info(clip: Clip):
    """
    Актуально для звуковых файлов по имени. Для видео пустые строки
    """
    series = ''
    scene = ''
    shot = ''
    take = ''

    if not clip.is_video():
        series, scene, shot, take = get_log_from_name(clip.id_[:-4])
        # print(clip.id_[:-4], end=', ')
        # print(f'seria {series}', end=', ')
        # print(f'scene {scene}', end=', ')
        # print(f'shot {shot}', end=', ')
        # print(f'take {take}', end=', ')
        # print()

        if not scene:
            scene = shot[:-2]
            shot = shot[-2:]
            print(f'{scene}, {shot}?')
            new_scene_shot = input()
            if new_scene_shot:
                scene_shot = new_scene_shot.split('_')
                scene = scene_shot[0]
                shot = scene_shot[1]

        take = take_correcting(take)
        shot = shot_correcting(shot)
        scene = scene_correcting(scene)
        series = series_correcting(series)

    clip.series = series
    clip.scene = scene
    clip.shot = shot
    clip.take = take


def _get_video_clips(clip_list: List[Clip]):
    for clip in clip_list:
        if clip.is_video():
            yield clip


def _get_audio_clips(clip_list: List[Clip]):
    for clip in clip_list:
        if not clip.is_video():
            yield clip


def set_video_name_by_audio(clip_list: List[Clip], date: datetime):
    prev_clip_name = ''

    for video_clip in _get_video_clips(clip_list):
        clip_name = ''
        for audio_clip in _get_audio_clips(clip_list):
            if not (video_clip.first_aux_frame > audio_clip.last_aux_frame or
                    video_clip.last_aux_frame < audio_clip.first_aux_frame):
                clip_name = f'{audio_clip.series}.{audio_clip.scene}_{audio_clip.shot}_{audio_clip.take}-' + \
                            date.strftime('%d%m%y') + 'm'
                video_clip.series = audio_clip.series
                video_clip.scene = audio_clip.scene
                video_clip.shot = audio_clip.shot
                video_clip.take = audio_clip.take
        if clip_name:
            if clip_name == prev_clip_name:
                clip_name += '_bis'
        video_clip.set_clip_name(clip_name)
        prev_clip_name = clip_name


def fix_duplicate_clip_id(clip_list: List[Clip]):
    clip_id_list = [clip.id_ for clip in clip_list]
    if len(clip_id_list) != len(set(clip_id_list)):
        duplicates = [k for k, v in Counter(clip_id_list).items() if v > 1]
        for duplicate in duplicates:
            selected_clips = [clip for clip in clip_list if clip.id_ == duplicate]
            for idx, clip in enumerate(selected_clips):
                clip.set_clip_name(f'{clip.id_}_{idx:02d}')


def make_xml_node(root: _Element, arguments: WorkArguments):
    bin_list_from_xml = [bin_.find('name').text for bin_ in root.iter('bin')]
    # print(bin_list_from_xml)
    clip_list = [Clip.Clip(clip) for clip in root.iter('clip')]

    delta = calculate_delta(clip_list, arguments)

    for clip in clip_list:
        insert_aux_timecode(clip, delta)
        set_log_info(clip)

    date = datetime.now()
    if arguments.next_day:
        date += timedelta(1)
    if arguments.prev_day:
        date -= timedelta(1)

    # rename video clip
    if arguments.rename:
        set_video_name_by_audio(clip_list, date)
        fix_duplicate_clip_id(clip_list)

    bin_dict = {}
    if arguments.bin:

        # create bins dictionary
        for clip in clip_list:
            bin_name = f'{clip.series}.{clip.scene}' if arguments.rename else bin_list_from_xml[0]
            if bin_name not in bin_dict:
                bin_dict.update({bin_name: []})
            bin_dict[bin_name].append(clip)

        if arguments.rename:
            for binKey in bin_dict.copy():
                print(binKey + '?')
                new_bin = input()
                if new_bin:
                    print('ups')
                    if new_bin[0] == '.':
                        series = binKey[:4]
                        new_bin = series + new_bin
                    series = new_bin[:4]
                    scenes = new_bin[5:]
                    for clip in _get_video_clips(bin_dict[binKey]):
                        clip_name = clip.id_
                        clip_name = series + '.' + scenes + clip_name[len(binKey):]
                        clip.series = series
                        clip.scene = scenes
                        clip.set_clip_name(clip_name)
                    if new_bin not in bin_dict:
                        bin_dict.update({new_bin: []})
                    bin_dict[new_bin].extend(bin_dict.pop(binKey))

            for binKey in bin_dict:
                print(binKey)

    if arguments.bin:
        bin_list = []
        for binKey in bin_dict:
            bin_node = Bin(name=binKey)
            for clip in bin_dict[binKey]:
                bin_node.add_children(clip)

            if arguments.merge:
                for video_clip in _get_video_clips(bin_dict[binKey]):
                    for audio_clip in _get_audio_clips(bin_dict[binKey]):
                        if video_clip.shot == audio_clip.shot and video_clip.take == audio_clip.take:
                            bin_node.add_children(merge(video_clip, audio_clip))

            bin_list.append(bin_node)
        return bin_list
    else:
        return clip_list


def get_xml_items(bin_list: List[_Element], arguments: WorkArguments) -> List:
    item_list = []
    for idx, batch_item in enumerate(bin_list):
        item = make_xml_node(batch_item, arguments)
        item_list.append(item)
    return item_list
