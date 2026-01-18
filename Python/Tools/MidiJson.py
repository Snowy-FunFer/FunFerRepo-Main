""" Python 3.13.5
这是Midi文件解析的辅助工具。
里面封装了一些常用的功能。
例如将Midi文件转化为可读的Json文件，
以及将Json文件重新编码为Midi文件。

"""

import json
import math
import mido
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def get_info_by_pitch(pitch: int) -> str:
	""" 根据MIDI音高编号(0-127)返回信息：pitch=60为中央C
	Args:
		pitch(int): MIDI音高编号（0-127）
	Returns:
		sci_pitch(str): 科学音高记法。如C4表示中央C
	Raises:
		IndexError: MIDI音高编号不在合理范围
	"""
	if pitch > 127 or pitch < 0:
		raise IndexError
	r = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][pitch % 12]  # 唱名
	q = pitch // 12 - 1  # 八度数
	return r + str(q)

def get_freq_by_pitch(pitch: int) -> float:
	""" 根据MIDI音高编号(0-127)返回频率
    Args:
        pitch(int): MIDI音高编号（0-127）
    Returns:
        freq(float): 频率（Hz）
    Raises:
        IndexError: MIDI音高编号不在合理范围
    """
	if pitch > 127 or pitch < 0:
		raise IndexError
	return 440 * 2 ** ((pitch - 69) / 12)

def get_pitch_by_freq(freq: float) -> int:
	""" 根据频率返回MIDI音高编号(0-127)
    Args:
        freq(float): 频率（Hz）
    Returns:
        pitch(int): MIDI音高编号（0-127）
    Raises:
        ValueError: 频率不在合理范围
    """
	if freq > 20000 or freq < 20:
		raise ValueError
	return round(69 + 12 * math.log2(freq / 440))

class MidiJson(object):
	""" midi处理工具类
	Attributes:
		midi_file(Path): midi文件路径
		note_json(dict): json格式的note数据信息
			note_json = {
				"metadata": {
					"export_date": "ISO格式的当前日期时间",
					"tracks_count": "MIDI文件中的音轨总数"
				},
				"tracks": [
					{
						"track_index": "音轨索引（从0开始）",
						"note_count": "该音轨中的音符数量",
						"programs_set": ["该音轨使用的乐器程序编号列表"],
						"pitch_range": {
							"min": "最低音高（如果没有音符则为null）",
							"max": "最高音高（如果没有音符则为null）"
						},
						"notes": [
							{
								"pitch": "MIDI音高编号（0-127）",
								"velocity": "音符力度（0-127）",
								"program": "乐器程序编号",
								"start": "开始时间（秒，保留3位小数）",
								"duration": "持续时间（秒，保留3位小数）"
							},
							// ... 更多音符
						]
					},
					// ... 更多音轨
				]
			}
	"""
	def __init__(self, input_file: Path | str):
		self.midi_file = Path(input_file)
		self.note_json = self.midi2json(self.midi_file)
		
	def write_in_json(self, output_file: Path | str) -> "MidiJson":
		""" 将note数据信息储存到外部json文件
		Args:
			output_file(Path | str): 输出的json文件路径
		Returns:
			self: 便于链式调用
		Raises:
			FileNotFoundError: 文件路径错误
		"""
		with open(output_file, 'w', encoding='utf-8') as f:
			json.dump(self.note_json, f, indent="\t", ensure_ascii=False)
		return self
		
	def json2midi(self, note_data: dict, output_file: Path | str=None) -> "MidiJson":
		""" 将json格式的note数据信息储存到midi文件
		Args:
			note_data(dict): json格式的note数据信息
			output_file(Path | str, optional): 输出的midi文件路径，为None则替换初始midi文件。默认为None
		Returns:
			self: 便于链式调用
		"""
		ticks_per_beat = 480
		mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
		tempo = 500000
		for track_data in note_data.get("tracks", []):
			track = mido.MidiTrack()
			mid.tracks.append(track)
			track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
			notes = sorted(track_data.get("notes", []), key=lambda n: n["start"])
			channel_programs = {}
			events = []
			for note in notes:
				start_time = note["start"]
				duration = note["duration"]
				pitch = note["pitch"]
				velocity = note["velocity"]
				program = note.get("program", 0)
				channel = 0
				for ch, prog in channel_programs.items():
					if prog == program:
						channel = ch
						break
				else:
					channel = len(channel_programs)
					if channel > 15:
						channel = 15
					channel_programs[channel] = program
				events.append(('note_on', start_time, channel, pitch, velocity, program))
				events.append(('note_off', start_time + duration, channel, pitch, 0, program))
			for channel, program in channel_programs.items():
				events.append(('program_change', 0, channel, None, None, program))
			events.sort(key=lambda e: e[1])
			last_time = 0.0
			for event_type, event_time, channel, pitch, velocity, program in events:
				delta_seconds = event_time - last_time
				delta_ticks = round(1000000 * ticks_per_beat * delta_seconds / tempo)
				if event_type == 'note_on':
					track.append(mido.Message('note_on', note=pitch, velocity=velocity, channel=channel, time=delta_ticks))
				elif event_type == 'note_off':
					track.append(mido.Message('note_off', note=pitch, velocity=velocity, channel=channel, time=delta_ticks))
				elif event_type == 'program_change':
					track.append(mido.Message('program_change', program=program, channel=channel, time=delta_ticks))
				last_time = event_time
		if output_file:
			mid.save(output_file)
		else:
			mid.save(self.midi_file)
		return self

	@staticmethod
	def midi2json(input_file: Path | str) -> dict:
		""" 将midi文件的note数据信息转化为json格式
		Args:
			input_file(Path | str): midi文件路径
		Returns:
			export_data(dict): json格式的note数据信息
		Raises:
			FileNotFoundError: 文件路径错误
		"""
		mid = mido.MidiFile(input_file)
		ticks_per_beat = mid.ticks_per_beat
		tempo_changes = [(0, 500000)]
		for track in mid.tracks:
			current_tick = 0
			for msg in track:
				current_tick += msg.time
				if msg.type == 'set_tempo':
					tempo_changes.append((current_tick, msg.tempo))
		tempo_changes.sort(key=lambda x: x[0])
		export_data = {
			"metadata": {
				"export_date": datetime.now().isoformat(),
				"tracks_count": len(mid.tracks)
			},
			"tracks": []
		}
		for track_idx, track in enumerate(mid.tracks):
			track_notes = []
			active_notes = defaultdict(list)
			current_programs = defaultdict(int)
			current_tick = 0
			current_time = 0.0
			tempo_index = 0
			used_programs = set()
			min_pitch = 128
			max_pitch = 0
			for msg in track:
				current_tick += msg.time
				while tempo_index + 1 < len(tempo_changes) and current_tick >= tempo_changes[tempo_index + 1][0]:
					segment_end = tempo_changes[tempo_index + 1][0]
					segment_ticks = segment_end - (current_tick - msg.time)
					tempo = tempo_changes[tempo_index][1]
					segment_seconds = (segment_ticks * tempo) / (ticks_per_beat * 1_000_000)
					current_time += segment_seconds
					tempo_index += 1
				tempo = tempo_changes[tempo_index][1]
				ticks_in_current = current_tick - max(current_tick - msg.time, tempo_changes[tempo_index][0])
				current_time += (ticks_in_current * tempo) / (ticks_per_beat * 1_000_000)
				if msg.type == 'program_change':
					current_programs[msg.channel] = msg.program
				if msg.type == 'note_on' and msg.velocity > 0:
					key = (msg.channel, msg.note)
					active_notes[key].append((current_time, msg.velocity, current_programs[msg.channel]))
				elif msg.type in ['note_off', 'note_on'] and (msg.velocity == 0 or msg.type == 'note_off'):
					key = (msg.channel, msg.note)
					if active_notes[key]:
						start_time, velocity, program = active_notes[key].pop(0)
						duration = round(current_time - start_time, 3)
						start = round(start_time, 3)
						used_programs.add(program)
						if msg.note < min_pitch: min_pitch = msg.note
						if msg.note > max_pitch: max_pitch = msg.note
						track_notes.append({
							"pitch": msg.note,
							"velocity": velocity,
							"program": program,
							"start": start,
							"duration": duration
						})
			track_data = {
				"track_index": track_idx,
				"note_count": len(track_notes),
				"programs_set": sorted(used_programs),
				"pitch_range": {
					"min": min_pitch if min_pitch < 128 else None,
					"max": max_pitch if max_pitch > 0 else None
				},
				"notes": sorted(track_notes, key=lambda n: n["start"])
			}
			export_data["tracks"].append(track_data)
		return export_data

