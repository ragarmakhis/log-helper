import uuid

from utils.fcpxml import MergedClip, Clip


def merge(video_clip: Clip, audio_clip: Clip):
    merge_name = get_merge_name(video_clip)
    duration = calculate_merge_duration(video_clip, audio_clip)
    rate = video_clip.rate
    merge_clip = MergedClip(merge_name, duration, rate)
    merge_clip.id_ = merge_name
    merge_clip.uuid_ = str(uuid.uuid4()).upper()
    merge_clip.in_ = -1
    merge_clip.out = -1
    merge_clip.masterclipid = merge_name
    merge_clip.ismasterclip = 'TRUE'
    merge_clip.logginginfo = video_clip.logginginfo
    merge_clip.labels = video_clip.labels
    merge_clip.comments = video_clip.comments
    offset = calculate_offset(video_clip, audio_clip)
    merge_clip.add_video_media(video_clip, offset)
    merge_clip.add_audio_media(audio_clip, offset)
    merge_clip.update_links()

    return merge_clip


def get_merge_name(clip):
    merge_name = f'{clip.id_} Merge'

    return merge_name


def calculate_merge_duration(video_clip, audio_clip):
    start_video_clip = video_clip.first_aux_frame
    start_audio_clip = audio_clip.first_aux_frame
    end_video_clip = start_video_clip + video_clip.duration
    end_audio_clip = start_audio_clip + audio_clip.duration

    start_merge_clip = start_audio_clip if start_audio_clip < start_video_clip else start_video_clip
    end_merge_clip = end_audio_clip if end_audio_clip > end_video_clip else end_video_clip
    return end_merge_clip - start_merge_clip


def calculate_offset(video_clip, audio_clip):
    """
    audio start offset relative to video
    """
    offset = audio_clip.first_aux_frame - video_clip.first_aux_frame
    # offset = audio_clip.get_timecode_frame('aux1') - video_clip.get_timecode_frame('aux1')
    return offset
