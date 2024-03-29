import astroplan
import astropy
import numpy
import os
import requests
from lxml import html
import re
import datetime

import datetime
import astropy.coordinates
import astropy.time
import astropy.units as u
from astropy.time import TimezoneInfo
import ephem
import numpy as np
from operator import itemgetter, attrgetter
from random import randint
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from rts2solib import rts2comm, queue
# from rts2solib import scriptcomm

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from io import BytesIO
import base64
from PIL import Image

class queue_obj:
	def __init__(self, name, ra, dec, priority, exp_objs, obj_type, obsreqid, rts2id, constraints=None, expids=[]):
		self.id = obsreqid
		self.rts2id = rts2id
		self.name = name
		self.ra = ra
		self.dec = dec
		self.priority = priority
		self.exp_objs = exp_objs
		self.obj_type = obj_type
		self.expids = expids
		#self.skycoord = astropy.coordinates.SkyCoord(
		#	ra=astropy.coordinates.Angle(self.ra),
		#	dec=astropy.coordinates.Angle(self.dec)
		#)
		self.skycoord = astropy.coordinates.SkyCoord(
			'{} {}'.format(self.ra, self.dec),
			unit=(u.hourangle, u.deg)
		)
		self.overhead = 0
		self.estimateoverhead()

		self.constraints = constraints
		self.constrained_visible = False

		self.altaz = None
		self.frame_airmass = None
		self.peak_airmass = None

		self.start_observation = None
		self.end_observation = None
		self.scheduled = False

		self.order = None
		self.rts2start_t = None
		self.rts2end_t = None
		self.db_starttime = None
		self.db_endtime = None
		self.db_log = ''


	def set_altaz(self, frame, setpeak=False):
		self.altaz = self.skycoord.transform_to(frame)
		airmasses = []
		for aa in self.altaz.secz:
			if aa > 1:
				airmasses.append(aa)

		if len(airmasses):
			if setpeak:
				self.peak_airmass = min(airmasses)
			self.frame_airmass = np.mean(airmasses)
			self.airmass_potential = self.peak_airmass-self.frame_airmass
		else:
			self.peak_airmass = 99
			self.frame_airmass = 99
			self.airmass_potential = 99


	def outputobjectinfo(self):
		print("Queue Object: {}".format(self.name))
		print("Type: {}".format(self.obj_type))
		print("RA: {}".format(self.ra))
		print("DEC: {}".format(self.dec))
		print("Est. Overhead: {}".format(self.overhead))
		print("Observation Infos")
		for obsinfo in self.exp_objs:
			print("     Filter: {}, Exposure Time: {}, Amount {}".format(obsinfo.filter, obsinfo.exptime, obsinfo.amount))

	def estimateoverhead(self, readout=10, slew_rate=60, filter_change_rate=15):
		#values are in seconds
		#initial overhead is the slewrate: 60 seconds
		t = slew_rate

		#add up all of the exposure times: sum(exposuretime*amount)
		exp_time = sum(float(x.exptime)*float(x.amount) for x in self.exp_objs)

		#apply readout times for every single exposure: readouttime*N_exposure
		read_outs = readout*sum(int(x.amount) for x in self.exp_objs)

		#apply filter change times
		filter_change_time = filter_change_rate*float(len(self.exp_objs))
		#add it all together
		t = t+exp_time+read_outs+filter_change_time

		self.overhead = t
		return t

	def evaluate_constraints(self, time, location, log):
		if self.constraints is not None:
			if self.constraints.moon_distance_threshold is not None:
				moon = astropy.coordinates.get_moon(time=time, location=location)
				sep = self.skycoord.separation(moon)/u.deg
				#print('Evaluating constraints moon distance: {}, {}>{}'.format(
				#	self.name,
				#	sep,
				#	self.constraints.moon_distance_threshold
				#))
				if sep > self.constraints.moon_distance_threshold:
					self.constrained_visible = True
				else:
					log.append('{} moon distance constrained! {}'.format(self.name, sep))
					self.constrained_visible = False
					return
			if self.constraints.airmass_threshold is not None:
				#print('Evaluating constraints airmass: {}, {}<{}'.format(
				#	self.name,
				#	self.frame_airmass,
				#	self.constraints.airmass_threshold
				#))
				if self.frame_airmass < self.constraints.airmass_threshold:
					self.constrained_visible = True
				else:
					log.append('{} airmass constrained! {}'.format(self.name, self.frame_airmass))
					self.constrained_visible = False
					return
		else:
			#no constraints -> it is visible
			self.constrained_visible = True


class exp_obj:
	def __init__(self, amount, filter, exptime, expid=None, obsreqid=None):
		self.amount = amount
		self.filter = filter
		self.exptime = exptime
		self.expid = expid
		self.dbid = obsreqid


class queue_obj_constraints:
	def __init__(self, moon_distance_threshold=10, airmass_threshold=2.0):
		self.moon_distance_threshold = moon_distance_threshold #arcseconds?
		self.airmass_threshold = airmass_threshold


def orp_session():
    orpdbpath = 'postgresql+psycopg2://artn:ArTn_520@scopenet.as.arizona.edu'
    engine = create_engine(orpdbpath)
    meta = MetaData()
    meta.reflect(bind=engine)
    session = sessionmaker(bind=engine)()

    return meta, session


def orp_targets(queued_iso=datetime.datetime(2021, 3, 22)):

	queued_iso_end = queued_iso + datetime.timedelta(days=6)
	meta, session = orp_session()
	obsreqs = meta.tables['obsreqs']
	obs_col = meta.tables['obsreqs'].columns
	db_resp = session.query(obsreqs).filter(
            obs_col['queued']==True,
            #obs_col['completed']==False,
            obs_col['queued_iso'] > queued_iso,
            obs_col['queued_iso'] < queued_iso_end
        ).all()
	return format_orp_targets(db_resp)

def format_orp_targets(obsreqs, exposures):
	'''Dirty way to group obsreqs'''

	
	return_data = []
	for ob in obsreqs:
		exp_reqs = [x for x in exposures if x.obsreqid == ob.id]
		observation_infos = []
		expids = []
		for e in exp_reqs:
			expids.append(int(e.id))
			observation_infos.append(
                    exp_obj(
                        e.num_exp,
                        e.filter_name,
                        e.exp_time,
						e.id,
						int(ob.id)
                    )
				)

		q = queue_obj(
                ob.object_name,
                ob.ra_hms,
                ob.dec_dms,
                5,
                observation_infos,
				'Object',
				ob.id,
				ob.rts2_id,
                queue_obj_constraints(
                    moon_distance_threshold=10,
                    airmass_threshold=2.5
                ),
                expids = expids
            )
		return_data.append(q)
	return return_data


def getCurrentQueue(telescope='Kuiper', queuename='plan'):
	if telescope == 'Kuiper':
		try:
			q = queue.Queue(queuename)
			q.load()
			return q.entries
		except:
			return []
	return []


class FFTarget():

    def __init__(self, targ, frame):
        self.id = targ[0][0]
        self.name = targ[0][1]
        self.ra = targ[0][2]
        self.dec = targ[0][3]

        self._setSkyCoord()
        self._setAltAz(frame)

    def _setSkyCoord(self):
        self.skycoord = astropy.coordinates.SkyCoord(ra = self.ra*u.degree, dec = self.dec*u.degree)

    def _setAltAz(self, frame):
        self.altaz = self.skycoord.transform_to(frame)

    def dump(self):
        for key, value in self.__dict__.items():
            print('{}: {}, {}'.format(key, value, type(value)))


def FocusRunDecider(frame, frame_night):
    FOCUS_FIELD_IDS = [3611, 3612, 3613, 3614, 3615, 3616, 3617, 3618, 3619, 3620, 3621, 3622, 3623, 3624]
    com = rts2comm()
    #tar = rts2_targets()
    focus_field_targets = {}

    for _id in FOCUS_FIELD_IDS:
        t = com.get_target(_id)
        fft = FFTarget(t, frame)
        secz = fft.altaz.secz

        if secz > 0.0 and secz < 3:
            print(secz, fft.name)
            focus_field_targets[str(secz)] = fft

    lowest_secz = min(list(focus_field_targets.keys()))
    focus_field = focus_field_targets[lowest_secz]

    return_field = queue_obj(
        focus_field.name,
        focus_field.ra, focus_field.dec,
        0,
        [
                exp_obj(2, 'V', 30, int(focus_field.id)),
        ],
		'Focus',
		focus_field.id,
		focus_field.id,
        queue_obj_constraints(
            moon_distance_threshold=1,
            airmass_threshold=float(3.0)
        ),
        expids = [focus_field.id]
    )
    return_field.skycoord = focus_field.skycoord
    return_field.set_altaz(frame_night, setpeak=True)

    return return_field


class ARTNScheduler():

	def __init__(self, targets, location, night, schedule_focus=True, simulate=False, queue_type=0, utcoffset=7*u.hour):

		self.targets = targets
		self.location = location
		self.night = night
		#self.midnight = astropy.time.Time('{}-{}-{} 00:00:00'.format(night.year, night.month, night.day)) + utcoffset
		self.midnight = astropy.time.Time('{}-{}-{} 23:59:59.9'.format(night.year, night.month, night.day)) + utcoffset
		self.utcoffset = utcoffset
		self.scheduled_focus = schedule_focus
		self.simulate = simulate
		self.queue_type = queue_type

		self.delta_midnight = np.linspace(-12, 12, 1000)
		day_times = self.midnight + self.delta_midnight*u.hour

		self.frame_night = astropy.coordinates.AltAz(
			obstime=day_times,
			location=self.location
		)

		self.sun_altaz = astropy.coordinates.get_sun(day_times).transform_to(self.frame_night)
		self.moon_altaz = astropy.coordinates.get_moon(day_times).transform_to(self.frame_night)
		
		self.nightrange = []
		self.sun_alt_beforemid = []
		self.astronomical_night = []
		for i,x in enumerate(self.sun_altaz.alt < 5*u.deg):
			if x:
				self.nightrange.append(self.delta_midnight[i])
				self.sun_alt_beforemid.append(x)
		
		for i,x in enumerate(self.sun_altaz.alt < -15*u.deg):
			if x:
				self.astronomical_night.append(self.delta_midnight[i])

		self.scheduled_targets = []
		self.encoded_chart = ''
		self.log = ['Initiating ARTN Scheduler for {}'.format(self.night)]
		self.html_log = ''

	def logdump(self):
		for l in self.log:
			print(l)

	def run(self):

		runlog = []
		self.log.append('Starting Scheduler for {}!'.format(self.night))

		#Setting the peak airmass for all targets throughout the night
		[t.set_altaz(self.frame_night, True) for t in self.targets]

		interval_run = 'half-hour'

		#The range of hours of observability
		hour_intervals = int(self.astronomical_night[len(self.astronomical_night)-1]-self.astronomical_night[0])
		if interval_run == 'half-hour':
			intervals = hour_intervals
			slices = int(len(self.astronomical_night)/intervals)
		else:
			intervals = hour_intervals
			slices = int(len(self.astronomical_night)/intervals)

		frames_range = self.astronomical_night*u.hour

		#set the first observation time to be the first timeslot
		#	of astronomical night
		right_now = datetime.datetime.now()

		tmptime = astropy.time.Time('{}-{}-{} {}:{}:{}'.format(right_now.year, right_now.month, right_now.day, right_now.hour, right_now.minute, right_now.second)) + self.utcoffset
		
		night_begin = self.midnight + frames_range[0]
		night_end = self.midnight + frames_range[len(frames_range)-1]

		#if the user sets the queue in the middle of the night, and not simulate it from the beginning
		#	this will set the initial obstime to be at the current executed time.
		if (tmptime > night_begin and tmptime < night_end) and not self.simulate:
			obs_time = tmptime
			self.log.append('Starting in the middle of the night. Initial obstime set at {}\n'.format(obs_time-self.utcoffset))
		else:
			obs_time = night_begin
			self.log.append('Simulating for the beginning of the night: initial obstime set at {}\n'.format(obs_time-self.utcoffset))

		#obs_time = astropy.time.Time('2021-09-17 07:44:07.000')
		unscheduled_targets = self.targets
		self.scheduled_targets = []

		#If the queue is ran in the middle of the night
		#	this bit of code finds the frame in which to start the observations
		start_itera = 0
		for itera in range(intervals):
			if (itera+1) == intervals:
				frame_hours = self.midnight + frames_range[itera*slices:]
			else:
				frame_hours = self.midnight + frames_range[itera*slices:(itera+1)*slices]
			print(obs_time, frame_hours[-1], frame_hours[0])
			if obs_time < frame_hours[-1] and obs_time > frame_hours[0]:
				print('iteration: {}'.format(itera))
				start_itera = itera
				break

		#obs_time = astropy.time.Time('2021-09-17 07:44:07.000')
		print(start_itera, intervals)
		#If the queue is ran in the middle of the night, this will force
		#	a focus field to start the observations if it is requested
		forcefocus = self.scheduled_focus and start_itera >= 1

		ni = start_itera -1
		times_range = self.midnight + frames_range

		#Changed to a while loop 
		order_iter = 0
		while obs_time < times_range[-1]:
			ni += 1

			#get all unscheduled targets
			unscheduled_targets = [t for t in unscheduled_targets if not t.scheduled]

			#find the hour intervals
			#	if it is the last interval
			#		get the whats left after the last slice
			#	else: get the appropriate slice
			if (ni+1) == intervals:
				frame_hours = self.midnight + frames_range[ni*slices:]
			else:
				frame_hours = self.midnight + frames_range[ni*slices:(ni+1)*slices]

			if not len(frame_hours):
				break

			#self.log.append('obstime: {}. Last Frame time: {}'.format(obs_time, frame_hours[-1]))

			#if the obstime inside the frame, begin scheduling
			if obs_time <= frame_hours[-1] and obs_time >= frame_hours[0]:
					
				#create a new frame based on the frame_hour slice
				#	and evaluate the altaz for each target in this frame
				frame = astropy.coordinates.AltAz(
					obstime=frame_hours,
					location=self.location
				)

				focus_frame = astropy.coordinates.AltAz(
					obstime=frame_hours[0],
					location=self.location
				)

				#for the 0th and middle hours: run a focus run
				if self.scheduled_focus:
					#if (ni == 0 or ni == int(intervals/2.0)) or forcefocus:
					if ni == 0 or forcefocus:
						try:
							focus_field = FocusRunDecider(focus_frame, self.frame_night)
							focus_field.set_altaz(self.frame_night, setpeak=True)
							unscheduled_targets.append(focus_field)
							forcefocus = False
						except:
							self.log.append('Error in communication with the ARTN Kuiper computer')

				[t.set_altaz(frame) for t in unscheduled_targets]

				#do something with constraints: boolean observable = T/F?
				for t in unscheduled_targets:
					t.evaluate_constraints(frame_hours[0], self.location, self.log)
					#t.evaluate_constraints(frame_hours[int(len(frame_hours)/2)], self.location, self.log)
					
				constrained_targets = [t for t in unscheduled_targets if t.constrained_visible]

				#Scheduling logic:
				#	loop over priorities
				#	group "constrained_visible" targets in that priority
				#	sort those grouped targets by priority then by airmass
				#	set thos at the top to be scheduled
				#	-> do it again through all priorities

				priority_range = [0,1,2,3,4,5]

				for p in priority_range:
					if obs_time > frame_hours[-1]:
						break

					#self.log.append('Priority Group: {}'.format(p))
					#This will group the targets based on priority
					#	allows for decimal priority as well
					priority_targs = [t for t in constrained_targets if t.priority > p-1 and t.priority <= p]

					#Sort the targets by their airmasss potential.
					sort_p_targs = sorted(priority_targs, key=attrgetter('airmass_potential'), reverse=True)
					
					for s in sort_p_targs:
						self.log.append("   {}: {}, {}, {}".format(s.name, s.frame_airmass, s.priority, s.constrained_visible))

					#loop over each of these sorted targets
					#	assigning the top target an observation slot
					for s in sort_p_targs:
						#set the start_time to be the current obs_time
						#	end_time to be the obstime+overhead
						#	set to be scheduled
						s.start_observation = obs_time
						s.end_observation = obs_time + s.overhead*u.second
						s.scheduled = True
						s.order = order_iter
						order_iter += 1

						self.log.append('{} scheduled: {} with overhead: {} at Priority {}'.format(
							s.name,
							s.frame_airmass,
							#s.start_observation,
							#s.end_observation,
							s.overhead,
							s.priority
						))
						self.scheduled_targets.append(s)

						#reset the current obs_time + smol overhead
						obs_time = s.end_observation+(1*u.minute)

						#if the obs_time is greater than the last time in the frame:
						#	break out of the priority loop and create a new frame block
						if obs_time > frame_hours[-1]:
							self.log.append("Iterating new frame, {}, {}".format(ni, intervals))
							break
						
				self.log.append("Iterating new frame, {}, {}".format(ni, intervals))

			# if the obstime isn't outside the frame, it needs to be iterated to be within the next frame (defined as tmp).
			#	This will set it to be within the next frame, if it exists, otherwise exits
			if obs_time < frame_hours[-1]:
				tmp = self.midnight + frames_range[(ni+1)*slices:(ni+2)*slices]
				if not len(tmp):
					break
				self.log.append('obstime needs to be iterated {} {}'.format(obs_time, tmp[0]))
				obs_time = tmp[0]

		#give back the scheduled targets
		self.log.append('\nEstimated Schedule (with times relative to local midnight)')
		self.html_log += '''
		<h4>Estimated Schedule</h4>
 		<table class="table table-striped table-bordered table-hover table-sm">
			<thead>
				<tr>
					<th><font color="blue">Object</font></th>
					<th><font color="blue">Start Time</font></th>
					<th><font color="blue">End Time</font></th>
					<th><font color="blue">Range (hr rel to midnight)</font></th>
					<th><font color="blue">Est. Overhead</font></th>
					<th><font color="blue">Type</font></th>
					<th><font color="blue">Priority</font></th>
				</tr>
			</thead>
			<tbody>
		'''
		for t in self.scheduled_targets:
			s_start = (t.start_observation-self.midnight).to('hour')/u.hour
			s_end = (t.end_observation-self.midnight).to('hour')/u.hour
			scheduled_time_range = np.linspace(s_start, s_end, 50)

			t.db_starttime = (t.start_observation-self.utcoffset).to_value('iso', subfmt='date_hms')
			t.db_endtime = (t.end_observation-self.utcoffset).to_value('iso', subfmt='date_hms')

			self.log.append('{}: {} - {}. {} {}'.format(
				t.name,
				round(float(scheduled_time_range[0]), 3),
				round(float(scheduled_time_range[-1]), 3),
				t.priority,
				t.obj_type,
			))
			formatted_range = '{} - {}'.format(round(float(scheduled_time_range[0]), 3),
									round(float(scheduled_time_range[-1]), 3))
			self.html_log += '''
			<tr>
				<td>{}</td>
				<td>{}</td>
				<td>{}</td>
				<td>{}</td>
				<td>{}</td>
				<td>{}</td>
				<td>{}</td>
			</tr>
			'''.format(t.name,t.start_observation-self.utcoffset, t.end_observation-self.utcoffset, formatted_range, t.overhead, t.obj_type, t.priority)

		self.html_log += '''
			</tbody>
			</table>
		'''

		self.unscheduled_targets =  [t for t in unscheduled_targets if not t.scheduled]
		self.log.append('\nUnscheduled Targets (See log for constraint details)')
		for t in self.unscheduled_targets:
			self.log.append('{}: {}, {}'.format(t.name, t.priority, t.peak_airmass))
		return self.scheduled_targets

	def submit_queue(self, telescope='Kuiper', set_queue='plan'):
		readout=10 #seconds
		slew_rate=60 		  #seconds
		filter_change_rate=20 #seconds

		if telescope == 'Kuiper':
			try:
				q = queue.Queue(set_queue)
				#0 is FIFO
				#5 is SET_TIMES
				q.queueing = self.queue_type 
				q.save()
				self.log.append('Submitting Schedule to RTS2 Queue')
				self.log.append('Clearing current Queue')
				q.load()
				q.clear()
				self.log.append('Scheduling')

				#Queue target with start and end times. Those must be specified in ctime (seconds from 1-1-1970).
				unixtime = astropy.time.Time('{}-{}-{} 00:00:00'.format(1970, 1, 1))
				print([t.rts2id for t in self.scheduled_targets])
				for t in self.scheduled_targets:
					rts2id = t.rts2id
					if self.queue_type == 0:
						q.add_target(rts2id)

					elif self.queue_type == 5:
						start = t.start_observation
						start_td = start - unixtime
						t_start = int(start_td.to_value('day')*24*60*60)

						for exp in t.exp_objs:
							#just pass in the rts2id
							#calculate the 
							start_td = start - unixtime
							e_start = int(start_td.to_value('day')*24*60*60)

							tmp_end = start + (exp.exptime*exp.amount + readout*exp.amount)*u.second
							end_td = tmp_end-unixtime
							e_end = int(end_td.to_value('day')*24*60*60)
							
							start = tmp_end + (filter_change_rate*u.second)

							t.rts2start_t = t_start
							t.rts2end_t = e_end

						q.add_target(rts2id, start=t_start, end=e_end)
					
			except:
				print('Error in communication with the ARTN Kuiper computer')
				self.log.append('Error in communication with the ARTN Kuiper computer')
				return False

			self.log.append('Queue populated')
			return True

	def plot(self):
		#fig = plt.figure(figsize=(11,7))
		fig = Figure(figsize=(8,4))
		canvas = FigureCanvas(fig)

		ax = fig.add_subplot(1,1,1)
		moon_delta_midnight = []
		moon_airmass = []
		for i,x in enumerate(self.moon_altaz.secz):
			if x <= 5 and x > 1.0:
				moon_delta_midnight.append(self.delta_midnight[i])
				moon_airmass.append(x)

		#plotting the beginning and ending of the astronomical night
		ax.axvline(x=self.astronomical_night[0], color='k', linestyle='-', linewidth=2)
		ax.text(self.astronomical_night[0]-0.7, 0.93, 'Night begin', fontsize=10)
		ax.axvline(x=self.astronomical_night[-1], color='k', linestyle='-', linewidth=2)
		ax.text(self.astronomical_night[-1]-0.7, 0.93, 'Night end', fontsize=10)

		#plot the moon line
		ax.plot(moon_delta_midnight, moon_airmass, 'w', label='Moon', linestyle='dashed')

		len_range = int(len(self.nightrange))
		mid_len_range = int(len(self.nightrange)/2)

		#plot the blue gradients for the astronomical night time
		for xi in range(0, mid_len_range+1):
			ax.fill_between(self.nightrange[xi:mid_len_range+1], 3, 1, self.sun_alt_beforemid[xi:mid_len_range+1], facecolor='blue', zorder=0, alpha=0.008)
		for xi in range(len_range, mid_len_range, -1):
			ax.fill_between(self.nightrange[mid_len_range:xi], 3, 1, self.sun_alt_beforemid[mid_len_range:xi], facecolor='blue', zorder=0, alpha=0.008)

		#plot the scheduled target info
		for t in self.scheduled_targets:
			t_altaz = t.skycoord.transform_to(self.frame_night)
			dm = [x for i,x in enumerate(self.delta_midnight) if t_altaz.secz[i] > 1 and t_altaz.secz[i] <= 3.5]
			cc = [x for x in t_altaz.secz if x > 1 and x <= 3.5]

			#plot the airmass chart
			ax.plot(dm, cc, label=t.name, linestyle='dashed')

			s_start = (t.start_observation-self.midnight).to('hour')/u.hour
			s_end = (t.end_observation-self.midnight).to('hour')/u.hour

			scheduled_time_range = np.linspace(s_start, s_end, 50)
			bool_range = [True for x in scheduled_time_range]
			#print(s_start, s_end, min(dm), max(dm), t.name)

			#this is happening because it is being set to observe outside its range of observability!!!!
			try:
				sc_aa_tmp = [x for i,x in enumerate(cc) if dm[i] > s_start and dm[i] < s_end]
				scheduled_altaz = np.linspace(sc_aa_tmp[0], sc_aa_tmp[-1], 50)
				ax.plot(scheduled_time_range, scheduled_altaz, color='red', linewidth=10, alpha=0.4)
			except:
				print("weird bug, yikes", t.name)

			#plot the observation range as a filled column
			ax.fill_between(scheduled_time_range, 3, 1, bool_range, facecolor='red', zorder=0, alpha=0.4)
			#plot the observation range on top of the airmass line

			ax.text((s_end+s_start)/2.0, 2.625, t.name, ha='center', va='center', rotation=90, size=9)

		fig.subplots_adjust(right=0.75)
		ax.legend(loc='upper left', bbox_to_anchor=(1, 1), borderaxespad=0.)
		ax.grid(True, color='k')
		ax.set_xlim(self.nightrange[0], self.nightrange[len(self.nightrange)-1])
		ax.set_ylim(3, 0.95)
		ax.set_xlabel('Hours from Observatory Midnight')
		ax.set_ylabel('Airmass')
		
		canvas.draw()
		buf = canvas.buffer_rgba()
		X = numpy.asarray(buf)

		tmpfile = BytesIO()

		fig.savefig(tmpfile, format="png")
		data = base64.b64encode(tmpfile.getbuffer()).decode("ascii")
		self.encoded_chart = data

def main():

	big2 = astropy.coordinates.EarthLocation.of_site('mtbigelow')
	targets = orp_targets()
	utcoffset = 7*astropy.units.hour
	d = datetime.datetime.now()-datetime.timedelta(days=1)

	test = ARTNScheduler(targets, big2, d)
	test.run()
	test.plot()
	test.chart.show()
	#test.logdump()
	
#main()
