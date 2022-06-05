import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from lxml import etree
from lxml.etree import _Element


class _Tag:
    def get_tag(self):
        return self.__class__.__name__.lower().lstrip('_')


class Node(_Tag, ABC):
    @abstractmethod
    def create_node(self) -> _Element:
        pass


@dataclass
class _Rate:
    ntsc: str = 'FALSE'
    timebase: int = 25


@dataclass
class _LoggingInfo:
    scene: str = ''
    shottake: str = ''
    lognote: str = ''
    good: str = 'FALSE'


@dataclass
class _Labels:
    label2: str = ''


@dataclass
class _Reel:
    name: str = ''


@dataclass
class _ItemHistory:
    uuid_: str = ''


@dataclass
class _SourceTrack:
    mediatype: str = ''
    trackindex: str = ''


@dataclass
class _SampleCharacteristics:
    width: str = ''
    height: str = ''
    samplerate: str = ''
    depth: str = ''


@dataclass
class _Parameter:
    name: str = ''
    parameterid: str = ''
    valuemin: str = ''
    valuemax: str = ''
    value: str = ''


@dataclass
class _Comments:
    mastercomment1: str = ''
    mastercomment2: str = ''
    mastercomment3: str = ''
    mastercomment4: str = ''


class Bin(Node):
    def __init__(self, uuid_=None, updatebehavior='add', name='', childrens=None):
        if not uuid_:
            uuid_ = str(uuid.uuid4()).upper()
        self.uuid_ = uuid_
        self.updatebehavior = updatebehavior
        self.name = name
        if not childrens:
            childrens = []
        self.childrens = childrens

    @classmethod
    def Bin(cls, tag):
        uuid_ = tag.find('uuid').text
        updatebehavior = tag.find('updatebehavior').text
        name = tag.find('name').text
        childrens = []
        for children in tag.findall('children'):
            if children.tag == 'clip':
                children = Clip.Clip(children)
            if children.tag == 'bin':
                children = Bin.Bin(children)
            childrens.append(children)
        return cls(uuid_, updatebehavior, name, childrens)

    def create_node(self):
        bin_node = etree.Element('bin')
        uuid_ = etree.SubElement(bin_node, 'uuid')
        uuid_.text = self.uuid_
        updatebehavior = etree.SubElement(bin_node, 'updatebehavior')
        updatebehavior.text = self.updatebehavior
        name = etree.SubElement(bin_node, 'name')
        name.text = self.name
        children_node = etree.SubElement(bin_node, 'children')
        for children in self.childrens:
            tag = children.get_tag()
            if tag == 'bin':
                children_node.append(children.create_node())
            elif tag == 'clip':
                children_node.append(children.create_node())

        return bin_node

    def add_children(self, children):
        self.childrens.append(children)


class _Timecode:
    def __init__(self, rate=_Rate(), string='00:00:00:00', frame=0, displayformat='NDF',
                 source='source'):
        self.rate = rate
        self.string = string
        self.frame = frame
        self.displayformat = displayformat
        self.source = source  #
        self.reel = None  #

    @property
    def rate(self):
        return self.__rate

    @rate.setter
    def rate(self, rate):
        self.__rate = rate

    @property
    def string(self):
        return self.__string

    @string.setter
    def string(self, string):
        self.__string = string
        self.__frame_by_string(string)

    @property
    def frame(self):
        return self.__frame

    @frame.setter
    def frame(self, frame):
        self.__frame = frame
        self.__string_by_frame(frame)

    @property
    def displayformat(self):
        return self.__displayformat

    @displayformat.setter
    def displayformat(self, displayformat):
        self.__displayformat = displayformat

    @property
    def source(self):
        return self.__source

    @source.setter
    def source(self, source):
        self.__source = source

    @property
    def reel(self):
        return self.__reel

    @reel.setter
    def reel(self, reel):
        self.__reel = reel

    @classmethod
    def Timecode(cls, tag):
        rate = _Rate(timebase=int(tag.find('rate').find('timebase').text))
        string = tag.find('string').text
        frame = tag.find('frame').text
        displayformat = tag.find('displayformat').text
        timecode = cls(rate, string, int(frame), displayformat)
        if tag.find('source') is not None:
            timecode.source = tag.find('source').text
        if tag.find('reel') is not None:
            timecode.reel = _Reel(tag.find('reel').find('name').text)

        return timecode

    def __string_by_frame(self, frame: int):
        time_base = self.rate.timebase
        seconds, frames = divmod(frame, time_base)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        self.__string = f'{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}'

    def __frame_by_string(self, string: str):
        time_base = self.rate.timebase
        t = string.split(':')
        self.__frame = ((int(t[0]) * 60 + int(t[1])) * 60 + int(t[2])) * time_base + int(t[3])

    def create_timecode_node(self):
        timecode_node = etree.Element('timecode')
        rate = etree.SubElement(timecode_node, 'rate')
        timebase = etree.SubElement(rate, 'timebase')
        timebase.text = str(self.rate.timebase)
        string = etree.SubElement(timecode_node, 'string')
        string.text = self.string
        frame = etree.SubElement(timecode_node, 'frame')
        frame.text = str(self.frame)
        displayformat = etree.SubElement(timecode_node, 'displayformat')
        displayformat.text = self.displayformat
        source = etree.SubElement(timecode_node, 'source')
        source.text = self.source
        if self.reel is not None:
            reel = etree.SubElement(timecode_node, 'reel')
            name = etree.SubElement(reel, 'name')
            name.text = self.reel.name

        return timecode_node


class _Metadata:
    def __init__(self, tag):
        self.storage = tag.find('storage').text
        self.key = tag.find('key').text
        self.size = tag.find('size').text
        self.type_ = tag.find('type').text
        self.value = tag.find('value').text

    def create_metadata_node(self):
        metadata_node = etree.Element('metadata')
        storage = etree.SubElement(metadata_node, 'storage')
        storage.text = self.storage
        key = etree.SubElement(metadata_node, 'key')
        key.text = self.key
        size = etree.SubElement(metadata_node, 'size')
        size.text = self.size
        type_ = etree.SubElement(metadata_node, 'type')
        type_.text = self.type_
        value = etree.SubElement(metadata_node, 'value')
        value.text = self.value

        return metadata_node


class _File:
    def __init__(self, id_):
        self.id_ = id_
        self.name = None
        self.pathurl = None
        self.rate = None
        self.duration = None
        self.metadatas = None
        self.timecodes = None
        self.medias = None

    @classmethod
    def File(cls, tag):
        ret = cls(tag.get('id'))
        if tag.find('name') is not None:
            ret.name = tag.find('name').text
        if tag.find('pathurl') is not None:
            ret.pathurl = tag.find('pathurl').text
        if tag.find('rate') is not None:
            ret.rate = _Rate(timebase=int(tag.find('rate').find('timebase').text))
        if tag.find('duration') is not None:
            ret.duration = tag.find('duration').text
        if tag.find('metadata') is not None:
            ret.metadatas = []
            for metadata in tag.findall('metadata'):
                ret.metadatas.append(_Metadata(metadata))
        if tag.find('timecode') is not None:
            ret.timecodes = {}
            for timecode in tag.findall('timecode'):
                source = timecode.find('source').text
                ret.timecodes.update({source: _Timecode.Timecode(timecode)})
        if tag.find('media') is not None:
            ret.medias = []
            # ret.medias = {}
            for media in tag.find('media').getchildren():
                if media.tag == 'video':
                    ret.medias.append(('video', _Video.Video(media)))
                if media.tag == 'audio':
                    ret.medias.append(('audio', _Audio.Audio(media)))

        return ret

    def create_file_node(self):
        file_node = etree.Element('file')
        file_node.set('id', self.id_)
        if self.name is not None:
            name = etree.SubElement(file_node, 'name')
            name.text = self.name
        if self.pathurl is not None:
            pathurl = etree.SubElement(file_node, 'pathurl')
            pathurl.text = self.pathurl
        if self.rate is not None:
            rate = etree.SubElement(file_node, 'rate')
            timebase = etree.SubElement(rate, 'timebase')
            timebase.text = str(self.rate.timebase)
        if self.duration is not None:
            duration = etree.SubElement(file_node, 'duration')
            duration.text = self.duration
        if self.metadatas is not None:
            for metadata in self.metadatas:
                file_node.append(metadata.create_metadata_node())
        if self.timecodes is not None:
            for key in self.timecodes:
                file_node.append(self.timecodes[key].create_timecode_node())
        if self.medias is not None:
            media_node = etree.SubElement(file_node, 'media')
            for media in self.medias:
                if media[0] == 'video':
                    media_node.append(media[1].create_video_node())
                if media[0] == 'audio':
                    media_node.append(media[1].create_audio_node())
            # if 'video' in self.medias:
            #     media_node.append(self.medias['video'].create_video_node())
            # if 'audio' in self.medias:
            #     media_node.append(self.medias['audio'].create_audio_node())

        return file_node


class _Link:
    def __init__(self, tag):
        self.linkclipref = tag.find('linkclipref').text
        self.mediatype = tag.find('mediatype').text
        self.trackindex = int(tag.find('trackindex').text)
        self.clipindex = int(tag.find('clipindex').text)
        if tag.find('groupindex') is not None:
            self.groupindex = int(tag.find('groupindex').text)

    def create_link_node(self):
        link_node = etree.Element('link')
        linkclipref = etree.SubElement(link_node, 'linkclipref')
        linkclipref.text = self.linkclipref
        mediatype = etree.SubElement(link_node, 'mediatype')
        mediatype.text = self.mediatype
        trackindex = etree.SubElement(link_node, 'trackindex')
        trackindex.text = str(self.trackindex)
        clipindex = etree.SubElement(link_node, 'clipindex')
        clipindex.text = str(self.clipindex)
        if hasattr(self, 'groupindex'):
            groupindex = etree.SubElement(link_node, 'groupindex')
            groupindex.text = str(self.groupindex)

        return link_node


class _Effect:
    def __init__(self, name, effectid, effectcategory, effecttype, mediatype, parameter):
        self.name = name
        self.effectid = effectid
        self.effectcategory = effectcategory
        self.effecttype = effecttype
        self.mediatype = mediatype
        self.parameter = parameter

    @classmethod
    def Effect(cls, tag):
        name = tag.find('name').text
        effectid = tag.find('effectid').text
        effectcategory = tag.find('effectcategory').text
        effecttype = tag.find('effecttype').text
        mediatype = tag.find('mediatype').text
        parameter = _Parameter(name=tag.find('parameter').find('name').text,
                               parameterid=tag.find('parameter').find('parameterid').text,
                               valuemin=tag.find('parameter').find('valuemin').text,
                               valuemax=tag.find('parameter').find('valuemax').text,
                               value=tag.find('parameter').find('value').text)

        return cls(name, effectid, effectcategory, effecttype, mediatype, parameter)

    def create_effect_node(self):
        effect_node = etree.Element('effect')
        name_effect = etree.SubElement(effect_node, 'name')
        name_effect.text = self.name
        effectid = etree.SubElement(effect_node, 'effectid')
        effectid.text = self.effectid
        effectcategory = etree.SubElement(effect_node, 'effectcategory')
        effectcategory.text = self.effectcategory
        effecttype = etree.SubElement(effect_node, 'effecttype')
        effecttype.text = self.effecttype
        mediatype = etree.SubElement(effect_node, 'mediatype')
        mediatype.text = self.mediatype
        parameter = etree.SubElement(effect_node, 'parameter')
        name_parameter = etree.SubElement(parameter, 'name')
        name_parameter.text = self.parameter.name
        parameterid = etree.SubElement(parameter, 'parameterid')
        parameterid.text = self.parameter.parameterid
        valuemin = etree.SubElement(parameter, 'valuemin')
        valuemin.text = self.parameter.valuemin
        valuemax = etree.SubElement(parameter, 'valuemax')
        valuemax.text = self.parameter.valuemax
        value = etree.SubElement(parameter, 'value')
        value.text = self.parameter.value

        return effect_node


class _Filter:
    def __init__(self, effects):
        self.effects = effects

    @classmethod
    def Filter(cls, tag):
        effects = []
        for effect in tag.findall('effect'):
            effects.append(_Effect.Effect(effect))

        return cls(effects)

    def create_filter_node(self):
        filter_node = etree.Element('filter')
        for effect in self.effects:
            filter_node.append(effect.create_effect_node())

        return filter_node


class _Clipitem:
    def __init__(self, id_, name, duration, rate, in_, out, start, end, masterclipid, logginginfo, labels, comments,
                 file, filters, sourcetrack, links, itemhistory):
        self.id_ = id_
        self.name = name
        self.duration = duration
        self.rate = rate
        self.in_ = in_
        self.out = out
        self.start = start
        self.end = end
        self.subframeoffset = None
        self.pixelaspectratio = None
        self.anamorphic = None
        self.alphatype = None
        self.masterclipid = masterclipid
        self.logginginfo = logginginfo
        self.labels = labels
        self.comments = comments
        self.file = file
        self.filters = filters
        self.sourcetrack = sourcetrack
        self.links = links
        self.fielddominance = None
        self.itemhistory = itemhistory

    @classmethod
    def Clipitem(cls, tag):
        id_ = tag.get('id')
        name = tag.find('name').text
        duration = tag.find('duration').text
        rate = _Rate(ntsc=tag.find('rate').find('ntsc').text,
                     timebase=tag.find('rate').find('timebase').text)
        in_ = tag.find('in').text
        out = tag.find('out').text
        start = tag.find('start').text
        end = tag.find('end').text
        masterclipid = tag.find('masterclipid').text
        logginginfo = _LoggingInfo(scene=tag.find('logginginfo').find('scene').text,
                                   shottake=tag.find('logginginfo').find('shottake').text,
                                   lognote=tag.find('logginginfo').find('lognote').text,
                                   good=tag.find('logginginfo').find('good').text)
        labels = _Labels(label2=tag.find('labels').find('label2').text)
        comments = _Comments(mastercomment1=tag.find('comments').find('mastercomment1').text,
                             mastercomment2=tag.find('comments').find('mastercomment2').text,
                             mastercomment3=tag.find('comments').find('mastercomment3').text,
                             mastercomment4=tag.find('comments').find('mastercomment4').text)
        file = _File.File(tag.find('file'))
        filters = []
        for filter_ in tag.findall('filter'):
            filters.append(_Filter.Filter(filter_))
        trackindex = ''
        if tag.find('sourcetrack').find('trackindex') is not None:
            trackindex = tag.find('sourcetrack').find('trackindex').text
        sourcetrack = _SourceTrack(mediatype=tag.find('sourcetrack').find('mediatype').text,
                                   trackindex=trackindex)
        links = []
        for link in tag.findall('link'):
            links.append(_Link(link))
        itemhistory = _ItemHistory(uuid_=tag.find('itemhistory').find('uuid').text)

        ret = cls(id_, name, int(duration), rate, int(in_), int(out), int(start), int(end), masterclipid, logginginfo,
                  labels, comments, file, filters, sourcetrack, links, itemhistory)
        if tag.find('subframeoffset') is not None:
            ret.subframeoffset = int(tag.find('subframeoffset').text)
        if tag.find('pixelaspectratio') is not None:
            ret.pixelaspectratio = tag.find('pixelaspectratio').text
        if tag.find('anamorphic') is not None:
            ret.anamorphic = tag.find('anamorphic').text
        if tag.find('alphatype') is not None:
            ret.alphatype = tag.find('alphatype').text
        if tag.find('fielddominance') is not None:
            ret.fielddominance = tag.find('fielddominance').text

        return ret

    def create_clipitem_node(self):
        clipitem_node = etree.Element('clipitem')
        clipitem_node.set('id', self.id_)
        name = etree.SubElement(clipitem_node, 'name')
        name.text = self.name
        duration = etree.SubElement(clipitem_node, 'duration')
        duration.text = str(self.duration)
        rate = etree.SubElement(clipitem_node, 'rate')
        ntsc = etree.SubElement(rate, 'ntsc')
        ntsc.text = self.rate.ntsc
        timebase = etree.SubElement(rate, 'timebase')
        timebase.text = self.rate.timebase
        in_ = etree.SubElement(clipitem_node, 'in')
        in_.text = str(self.in_)
        out = etree.SubElement(clipitem_node, 'out')
        out.text = str(self.out)
        start = etree.SubElement(clipitem_node, 'start')
        start.text = str(self.start)
        end = etree.SubElement(clipitem_node, 'end')
        end.text = str(self.end)
        if self.subframeoffset is not None:
            subframeoffset = etree.SubElement(clipitem_node, 'subframeoffset')
            subframeoffset.text = str(self.subframeoffset)
        if self.pixelaspectratio is not None:
            pixelaspectratio = etree.SubElement(clipitem_node, 'pixelaspectratio')
            pixelaspectratio.text = self.pixelaspectratio
        if self.anamorphic is not None:
            anamorphic = etree.SubElement(clipitem_node, 'anamorphic')
            anamorphic.text = self.anamorphic
        if self.alphatype is not None:
            alphatype = etree.SubElement(clipitem_node, 'alphatype')
            alphatype.text = self.alphatype
        masterclipid = etree.SubElement(clipitem_node, 'masterclipid')
        masterclipid.text = self.masterclipid
        logginginfo = etree.SubElement(clipitem_node, 'logginginfo')
        scene = etree.SubElement(logginginfo, 'scene')
        scene.text = self.logginginfo.scene
        shottake = etree.SubElement(logginginfo, 'shottake')
        shottake.text = self.logginginfo.shottake
        lognote = etree.SubElement(logginginfo, 'lognote')
        lognote.text = self.logginginfo.lognote
        good = etree.SubElement(logginginfo, 'good')
        good.text = self.logginginfo.good
        labels = etree.SubElement(clipitem_node, 'labels')
        label2 = etree.SubElement(labels, 'label2')
        label2.text = self.labels.label2
        comments = etree.SubElement(clipitem_node, 'comments')
        mastercomment1 = etree.SubElement(comments, 'mastercomment1')
        mastercomment1.text = self.comments.mastercomment1
        mastercomment2 = etree.SubElement(comments, 'mastercomment2')
        mastercomment2.text = self.comments.mastercomment2
        mastercomment3 = etree.SubElement(comments, 'mastercomment3')
        mastercomment3.text = self.comments.mastercomment3
        mastercomment4 = etree.SubElement(comments, 'mastercomment4')
        mastercomment4.text = self.comments.mastercomment4
        clipitem_node.append(self.file.create_file_node())
        for filter_ in self.filters:
            clipitem_node.append(filter_.create_filter_node())
        if self.sourcetrack is not None:
            sourcetrack = etree.SubElement(clipitem_node, 'sourcetrack')
            mediatype = etree.SubElement(sourcetrack, 'mediatype')
            mediatype.text = self.sourcetrack.mediatype
            if self.sourcetrack.trackindex:
                trackindex = etree.SubElement(sourcetrack, 'trackindex')
                trackindex.text = self.sourcetrack.trackindex
        for link in self.links:
            clipitem_node.append(link.create_link_node())
        if self.fielddominance is not None:
            fielddominance = etree.SubElement(clipitem_node, 'fielddominance')
            fielddominance.text = self.fielddominance
        itemhistory = etree.SubElement(clipitem_node, 'itemhistory')
        uuid_ = etree.SubElement(itemhistory, 'uuid')
        uuid_.text = self.itemhistory.uuid_

        return clipitem_node


class _Track:
    def __init__(self, tag):
        self.clipitem = _Clipitem.Clipitem(tag.find('clipitem'))
        self.enabled = tag.find('enabled').text
        self.locked = tag.find('locked').text

    def create_track_node(self):
        track_node = etree.Element('track')
        track_node.append(self.clipitem.create_clipitem_node())
        enabled_node = etree.SubElement(track_node, 'enabled')
        enabled_node.text = self.enabled
        locked_node = etree.SubElement(track_node, 'locked')
        locked_node.text = self.locked

        return track_node


class _Video(_Tag):
    def __init__(self):
        self.track = None
        self.duration = None
        self.samplecharacteristics = None

    @classmethod
    def Video(cls, tag):
        ret = cls()
        if tag.find('track') is not None:
            ret.track = _Track(tag.find('track'))
        if tag.find('duration') is not None:
            ret.duration = int(tag.find('duration').text)
        if tag.find('samplecharacteristics') is not None:
            ret.samplecharacteristics \
                = _SampleCharacteristics(width=tag.find('samplecharacteristics').find('width').text,
                                         height=tag.find('samplecharacteristics').find('height').text)

        return ret

    def create_video_node(self):
        video_node = etree.Element('video')
        if self.track is not None:
            video_node.append(self.track.create_track_node())
        if self.duration is not None:
            duration = etree.SubElement(video_node, 'duration')
            duration.text = str(self.duration)
        if self.samplecharacteristics is not None:
            samplecharacteristics = etree.SubElement(video_node, 'samplecharacteristics')
            width = etree.SubElement(samplecharacteristics, 'width')
            width.text = self.samplecharacteristics.width
            height = etree.SubElement(samplecharacteristics, 'height')
            height.text = self.samplecharacteristics.height

        return video_node


class _Audio(_Tag):
    def __init__(self):
        self.in_ = None
        self.out = None
        self.tracks = None
        self.samplecharacteristics = None
        self.channelcount = None
        self.__filter_ = None

    @classmethod
    def Audio(cls, tag):
        ret = cls()
        if tag.find('in') is not None:
            ret.in_ = int(tag.find('in').text)
        if tag.find('out') is not None:
            ret.out = int(tag.find('out').text)
        if tag.find('track') is not None:
            ret.tracks = []
            for track in tag.findall('track'):
                ret.tracks.append(_Track(track))
        if tag.find('samplecharacteristics') is not None:
            ret.samplecharacteristics \
                = _SampleCharacteristics(samplerate=tag.find('samplecharacteristics').find('samplerate').text,
                                         depth=tag.find('samplecharacteristics').find('depth').text)
        if tag.find('channelcount') is not None:
            ret.channelcount = int(tag.find('channelcount').text)

        return ret

    @property
    def track(self):
        return self.tracks[0]

    @property
    def filter_(self):
        return self.__filter_

    @filter_.setter
    def filter_(self, filter_):
        self.__filter_ = filter_

    def create_audio_node(self):
        audio_node = etree.Element('audio')
        if self.in_ is not None:
            in_node = etree.SubElement(audio_node, 'in')
            in_node.text = f'{self.in_}'
        if self.out is not None:
            out_node = etree.SubElement(audio_node, 'out')
            out_node.text = f'{self.out}'
        if self.tracks is not None:
            for track in self.tracks:
                audio_node.append(track.create_track_node())
        if self.samplecharacteristics is not None:
            samplecharacteristics = etree.SubElement(audio_node, 'samplecharacteristics')
            samplerate = etree.SubElement(samplecharacteristics, 'samplerate')
            samplerate.text = self.samplecharacteristics.samplerate
            depth = etree.SubElement(samplecharacteristics, 'depth')
            depth.text = self.samplecharacteristics.depth
        if self.channelcount is not None:
            channelcount = etree.SubElement(audio_node, 'channelcount')
            channelcount.text = f'{self.channelcount}'

        return audio_node


class Clip(Node):
    def __init__(self, name, duration, rate):
        self.id_ = None
        self.uuid_ = None
        self.updatebehavior = None
        self.name = name
        self.duration = duration
        self.rate = rate
        self.in_ = None
        self.out = None
        self.masterclipid = None
        self.ismasterclip = None
        self.logginginfo = None
        self.labels = None
        self.comments = None
        self.medias = None
        self.__series_scene_delimiter = '.'
        self.__shot_take_delimiter = '_'
        self.__scene_shot_delimiter = '_'

    @classmethod
    def Clip(cls, clip):
        id_ = clip.get('id')
        uuid_ = clip.find('uuid').text
        updatebehavior = clip.find('updatebehavior').text
        name = clip.find('name').text
        duration = clip.find('duration').text
        rate = _Rate(ntsc=clip.find('rate').find('ntsc').text,
                     timebase=clip.find('rate').find('timebase').text)
        in_ = clip.find('in').text
        out = clip.find('out').text
        masterclipid = clip.find('masterclipid').text
        ismasterclip = clip.find('ismasterclip').text
        logginginfo = _LoggingInfo(scene=clip.find('logginginfo').find('scene').text,
                                   shottake=clip.find('logginginfo').find('shottake').text,
                                   lognote=clip.find('logginginfo').find('lognote').text,
                                   good=clip.find('logginginfo').find('good').text)
        labels = _Labels(label2=clip.find('labels').find('label2').text)
        comments = _Comments(mastercomment1=clip.find('comments').find('mastercomment1').text,
                             mastercomment2=clip.find('comments').find('mastercomment2').text,
                             mastercomment3=clip.find('comments').find('mastercomment3').text,
                             mastercomment4=clip.find('comments').find('mastercomment4').text)
        medias = {}
        children = clip.find('media').getchildren()
        for media in children:
            if media.tag == 'video':
                medias.update({'video': _Video.Video(media)})
            if media.tag == 'audio':
                medias.update({'audio': _Audio.Audio(media)})
        # ret.medias = []
        # # ret.medias = {}
        # for media in tag.find('media').getchildren():
        #     if media.tag == 'video':
        #         ret.medias.append(('video', _Video.Video(media)))
        #     if media.tag == 'audio':
        #         ret.medias.append(('audio', _Audio.Audio(media)))

        ret = cls(name, int(duration), rate)
        ret.id_ = id_
        ret.uuid_ = uuid_
        ret.updatebehavior = updatebehavior
        ret.in_ = int(in_)
        ret.out = int(out)
        ret.masterclipid = masterclipid
        ret.ismasterclip = ismasterclip
        ret.logginginfo = logginginfo
        ret.labels = labels
        ret.comments = comments
        ret.medias = medias

        return ret

    @property
    def id_(self):
        return self.__id_

    @id_.setter
    def id_(self, id_):
        self.__id_ = id_

    @property
    def uuid_(self):
        return self.__uuid_

    @uuid_.setter
    def uuid_(self, uuid_):
        self.__uuid_ = uuid_

    @property
    def updatebehavior(self):
        return self.__updatebehavior

    @updatebehavior.setter
    def updatebehavior(self, updatebehavior):
        self.__updatebehavior = updatebehavior

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def duration(self):
        return self.__duration

    @duration.setter
    def duration(self, duration):
        self.__duration = duration

    @property
    def rate(self):
        return self.__rate

    @rate.setter
    def rate(self, rate):
        # if rate is None:
        #     rate = _Rate()
        self.__rate = rate

    @property
    def in_(self):
        return self.__in_

    @in_.setter
    def in_(self, in_):
        self.__in_ = in_

    @property
    def out(self):
        return self.__out

    @out.setter
    def out(self, out):
        self.__out = out

    @property
    def masterclipid(self):
        return self.__masterclipid

    @masterclipid.setter
    def masterclipid(self, masterclipid):
        self.__masterclipid = masterclipid

    @property
    def ismasterclip(self):
        return self.__ismasterclip

    @ismasterclip.setter
    def ismasterclip(self, ismasterclip):
        self.__ismasterclip = ismasterclip

    @property
    def logginginfo(self):
        return self.__logginginfo

    @logginginfo.setter
    def logginginfo(self, logginginfo):
        # if logginginfo is None:
        #     logginginfo = _LoggingInfo()
        self.__logginginfo = logginginfo

    @property
    def labels(self):
        return self.__labels

    @labels.setter
    def labels(self, labels):
        self.__labels = labels

    @property
    def comments(self):
        return self.__comments

    @comments.setter
    def comments(self, comments):
        self.__comments = comments

    @property
    def medias(self):
        return self.__medias

    @medias.setter
    def medias(self, medias):
        self.__medias = medias

    @property
    def file_name(self):
        media = self.get_main_media()
        return media.track.clipitem.file.name

    @property
    def series(self):
        return self.get_log()[0].split(self.__series_scene_delimiter)[0]

    @series.setter
    def series(self, series):
        self.logginginfo.scene = f'{series}{self.__series_scene_delimiter}{self.scene}'

    @property
    def scene(self):
        logginginfo_scene_split = self.get_log()[0].split(self.__series_scene_delimiter)
        len_first_element = len(logginginfo_scene_split[0])
        len_delimiter = len(self.__series_scene_delimiter)
        return self.get_log()[0][len_first_element + len_delimiter:]

    @scene.setter
    def scene(self, scene):
        self.logginginfo.scene = f'{self.series}{self.__series_scene_delimiter}{scene}'

    @property
    def shot(self):
        return self.get_log()[1].split(self.__shot_take_delimiter)[0]

    @shot.setter
    def shot(self, shot):
        self.logginginfo.shottake = f'{shot}{self.__shot_take_delimiter}{self.take}'

    @property
    def take(self):
        logginginfo_shottake_split = self.get_log()[1].split(self.__shot_take_delimiter)
        len_first_element = len(logginginfo_shottake_split[0])
        len_delimiter = len(self.__shot_take_delimiter)
        return self.get_log()[1][len_first_element + len_delimiter:]

    @take.setter
    def take(self, take):
        self.logginginfo.shottake = f'{self.shot}{self.__shot_take_delimiter}{take}'

    @property
    def first_aux_frame(self):
        # ret = self.get_timecode_frame('aux1') if self.get_timecode_frame('aux1') else 0
        # if self.get_timecode_frame('aux1'):
        #     ret = self.get_timecode_frame('aux1')
        # else:
        #     ret = 0
        # return ret
        return self.get_timecode_frame('aux1') if self.get_timecode_frame('aux1') else 0

    @property
    def last_aux_frame(self):
        return self.first_aux_frame + self.duration

    def __repr__(self):
        return f'id = {self.id_}, series = {self.series}, scene = {self.scene}, shot = {self.shot}, take = {self.take}'

    def get_timecode_frame(self, timecode_source):
        media = self.get_main_media()
        timecodes = media.track.clipitem.file.timecodes
        if not timecodes:
            return None

        # if hasattr(media, 'track'):
        #     track = media.track
        # else:
        #     track = media.tracks[0]
        return timecodes[timecode_source].frame if timecode_source in timecodes else None

    def is_video(self):
        return self.get_main_media().get_tag() == 'video'

    def remove_timecode(self, timecode_source):
        media = self.get_main_media()
        if media.track.clipitem.file.timecodes:
            media.track.clipitem.file.timecodes.pop(timecode_source, None)

    def insert_timecode(self, frame, timecode_source, reel_name=None):
        timecode = _Timecode()
        timecode.frame = frame
        timecode.source = timecode_source
        if reel_name:
            if timecode.reel is None:
                timecode.reel = _Reel()
            timecode.reel.name = reel_name

        media = self.get_main_media()
        if not media.track.clipitem.file.timecodes:
            media.track.clipitem.file.timecodes = {}
        media.track.clipitem.file.timecodes.update({timecode_source: timecode})

    def get_log(self):
        log_scene = ''
        if self.logginginfo.scene:
            log_scene = self.logginginfo.scene
        log_shottake = ''
        if self.logginginfo.shottake:
            log_shottake = self.logginginfo.shottake
        return log_scene, log_shottake

    def create_node(self):
        clip_node = etree.Element('clip')
        clip_node.set('id', self.id_)
        uuid_ = etree.SubElement(clip_node, 'uuid')
        uuid_.text = self.uuid_
        updatebehavior = etree.SubElement(clip_node, 'updatebehavior')
        updatebehavior.text = self.updatebehavior
        name = etree.SubElement(clip_node, 'name')
        name.text = self.name
        duration = etree.SubElement(clip_node, 'duration')
        duration.text = str(self.duration)
        rate = etree.SubElement(clip_node, 'rate')
        ntsc = etree.SubElement(rate, 'ntsc')
        ntsc.text = self.rate.ntsc
        timebase = etree.SubElement(rate, 'timebase')
        timebase.text = self.rate.timebase
        in_ = etree.SubElement(clip_node, 'in')
        in_.text = str(self.in_)
        out = etree.SubElement(clip_node, 'out')
        out.text = str(self.out)
        masterclipid = etree.SubElement(clip_node, 'masterclipid')
        masterclipid.text = self.masterclipid
        ismasterclip = etree.SubElement(clip_node, 'ismasterclip')
        ismasterclip.text = self.ismasterclip
        logginginfo = etree.SubElement(clip_node, 'logginginfo')
        scene = etree.SubElement(logginginfo, 'scene')
        scene.text = self.logginginfo.scene
        shottake = etree.SubElement(logginginfo, 'shottake')
        shottake.text = self.logginginfo.shottake
        lognote = etree.SubElement(logginginfo, 'lognote')
        lognote.text = self.logginginfo.lognote
        good = etree.SubElement(logginginfo, 'good')
        good.text = self.logginginfo.good
        labels = etree.SubElement(clip_node, 'labels')
        label2 = etree.SubElement(labels, 'label2')
        label2.text = self.labels.label2
        comments = etree.SubElement(clip_node, 'comments')
        mastercomment1 = etree.SubElement(comments, 'mastercomment1')
        mastercomment1.text = self.comments.mastercomment1
        mastercomment2 = etree.SubElement(comments, 'mastercomment2')
        mastercomment2.text = self.comments.mastercomment2
        mastercomment3 = etree.SubElement(comments, 'mastercomment3')
        mastercomment3.text = self.comments.mastercomment3
        mastercomment4 = etree.SubElement(comments, 'mastercomment4')
        mastercomment4.text = self.comments.mastercomment4
        media_node = etree.SubElement(clip_node, 'media')
        if 'video' in self.medias:
            media_node.append(self.medias['video'].create_video_node())
        if 'audio' in self.medias:
            media_node.append(self.medias['audio'].create_audio_node())
        # if self.medias is not None:
        #     media_node = etree.SubElement(file_node, 'media')
        #     for media in self.medias:
        #         if media[0] == 'video':
        #             media_node.append(media[1].create_video_node())
        #         if media[0] == 'audio':
        #             media_node.append(media[1].create_audio_node())

        return clip_node

    def get_main_media(self):
        if 'video' in self.medias:
            return self.medias['video']
        else:
            return self.medias['audio']

    def set_clip_name(self, clip_name):
        if clip_name:
            filename = self.file_name[:-4]

            # meta
            self.id_ = clip_name
            self.name = clip_name
            self.masterclipid = clip_name

            # video
            if self.is_video():
                self.medias['video'].track.clipitem.id_ = clip_name + '1'
                self.medias['video'].track.clipitem.name = clip_name
                self.medias['video'].track.clipitem.masterclipid = clip_name
                self.medias['video'].track.clipitem.file.id_ = filename
                links = self.medias['video'].track.clipitem.links
                for count, link in enumerate(links):
                    link.linkclipref = clip_name + str(count + 1)

            # audio
            if 'audio' in self.medias:
                for count, track in enumerate(self.medias['audio'].tracks):
                    track.clipitem.id_ = clip_name + str(count + 2)
                    track.clipitem.name = clip_name
                    track.clipitem.masterclipid = clip_name
                    track.clipitem.file.id_ = filename
                    links = track.clipitem.links
                    for count_link, link in enumerate(links):
                        link.linkclipref = clip_name + str(count_link + 1)


class MergedClip(Clip):
    def add_video_media(self, clip, offset):
        if not self.medias:
            self.medias = {}
        if not clip.is_video() or 'video' in self.medias:
            return
        self.medias.update({'video': clip.medias['video']})
        video_track = self.medias['video'].track
        clip_item = video_track.clipitem
        clip_item.id_ = f'{self.name}1'
        clip_item.name = self.name
        clip_item.start = self.in_ - offset
        clip_item.end = self.out - offset
        clip_item.masterclipid = self.name
        clip_item.syncoffset = 0
        clip_item.file = _File(clip.file_name[:-4])

        video_track.enabled = 'TRUE'
        video_track.locked = 'FALSE'
        if 'audio' not in self.medias:
            self.add_audio_media(clip, offset)

        # self.update_links()

    def add_audio_media(self, clip, offset):
        self_tracks = self.medias['audio'].tracks if 'audio' in self.medias else []
        clip_tracks = clip.medias['audio'].tracks if 'audio' in clip.medias else []
        tracks = []
        if clip.is_video():
            tracks.extend(clip_tracks)
            number_of_first_tracks = len(clip_tracks)
            tracks.extend(self_tracks)
        else:
            tracks.extend(self_tracks)
            number_of_first_tracks = len(self_tracks)
            tracks.extend(clip_tracks)
        for ind, track in enumerate(tracks):
            track.clipitem.id_ = f'{self.name}{2+ind}'
            track.clipitem.name = self.name
            if ind < number_of_first_tracks:
                track.clipitem.start = self.in_ - offset
                track.clipitem.end = self.out - offset
                track.clipitem.syncoffset = 0
            else:
                track.clipitem.start = self.in_
                track.clipitem.end = self.out
                track.clipitem.syncoffset = offset
            track.clipitem.subframeoffset = 0
            track.clipitem.masterclipid = self.name
            track.enable = 'TRUE'
            track.enable = 'FALSE'
        media = _Audio()
        media.in_ = -1
        media.out = -1
        media.tracks = tracks
        parameter = _Parameter('Level', 'level', '0', '3.98109', '1')
        effect = _Effect('Audio Levels', 'audiolevels', 'audiolevels', 'audiolevels', 'audio', parameter)
        media.filter_ = _Filter([effect])
        self.medias['audio'] = media

        # self.update_links()

    def generate_links(self):
        return self

    def update_links(self):
        first_links = self.medias['audio'].tracks[0].clipitem.links
        second_links = self.medias['audio'].tracks[-1].clipitem.links
        links = first_links[:]
        links.extend(second_links)
        for ind, link in enumerate(links):
            link.linkclipref = f'{self.name}{1+ind}'
            if ind != 0:
                link.trackindex = ind
        self.medias['video'].track.clipitem.links = links
        for track in self.medias['audio'].tracks:
            track.clipitem.links = links
