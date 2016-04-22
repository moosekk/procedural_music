import midi, itertools, random, numpy, sys, collections, os, math, array, subprocess
from itertools import *
from itertools import izip_longest as zip
r=44000
def gain(s, v): return (x * v for x in s)
def chunk(seq, n): it = iter(seq); return iter(lambda: list(islice(it, 0, n)), [])
def groupby(seq, f): return itertools.groupby(sorted(seq,key=f), f)
def tone(freq, dur=1, delay=0):
    o = random.random() * 10; freq *= (1 + random.random() * 0.00001);
    return (0.5 + 0.5 * math.sin(freq * t * 6.28 / r + o) for t in range(int(dur * r)))
def add(*items): return (sum(x) * 1.0 / len(items) for x in zip(*items, fillvalue=0))
def notesToWave(notes): return (x for n in notes for x in (tone(n[0], n[1]) if n else tone(0, 1)))

sox = subprocess.Popen("sox -q -v 1 -traw -r44000 -b16 -eunsi - -tcoreaudio".split(), stdin=subprocess.PIPE)
def play(tone, oo=sox.stdin):
    def s(v, mv=65535): return int(v * mv)
    for tone in chunk(tone, 1000):
        data = array.array('H', map(s, tone))
        oo.write(data.tostring())

class SongModel:
    def __init__(self, midifile):
        self.midi = midi.read_midifile(midifile)
        self.midi.make_ticks_abs()
        self.tracks = { t.name : t for t in map(TrackModel, self.midi) }
    def _play(self): play(add(*(notesToWave(t.generate()) for t in self.tracks.values())))

class TrackModel:
    def __init__(self, track):
        notes = [n for n in track if isinstance(n, midi.NoteOnEvent)]
        noteup = [n for n in track if isinstance(n, midi.NoteOffEvent)]
        try :
            tempo = next((n for n in track if isinstance(n, midi.SetTempoEvent)))
            tickrate = tempo.bpm * 60
        except: tickrate = 400
        for n in notes:
            off = next((x for x in noteup if x.pitch == n.pitch and x.tick > n.tick), None)
            n.duration = min(8, (off.tick - n.tick) * 1.0 / tickrate) if off else 0.2
            n.tone = 440 * 2 ** ((n.pitch - 69) * 1.0 / 12)
        if not notes: self.model = {}; self.name = '_'; return
        notes = [(n.tone, n.duration, n.pitch) for n in notes]
        note3 = [((a,b),c) for a,b,c in zip(notes, notes[1:], notes[2:])]
        keys = groupby(note3, lambda (a,c): a)
        self.model = {k:collections.Counter(x[1] for x in v) for k, v in keys}
        try : self.name = next(x.text.strip() for x in track if isinstance(x, midi.TrackNameEvent))
        except: self.name = '_'
        self.notes = notes
    def generate(self):
        if not self.model: return
        state = random.choice(self.model.keys())
        while True:
            yield state[0]
            try: newnote = (random.choice(self.model[state].keys()),)
            except: newnote = (random.choice(self.model.keys())[0],)
            state = state[1:] + newnote

ff = SongModel(sys.argv[1] if len(sys.argv)>1 else 'canon.mid')
print >> sys.stderr,  '\n'.join(ff.tracks)
ff._play()
