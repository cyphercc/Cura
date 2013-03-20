from __future__ import absolute_import

import wx
import os
import webbrowser

from Cura.gui import configBase
from Cura.gui import expertConfig
from Cura.gui import preview3d
from Cura.gui import sliceProgressPanel
from Cura.gui import alterationPanel
from Cura.gui import pluginPanel
from Cura.gui import preferencesDialog
from Cura.gui import configWizard
from Cura.gui import firmwareInstall
from Cura.gui import printWindow
from Cura.gui import simpleMode
from Cura.gui import projectPlanner
from Cura.gui.tools import batchRun
from Cura.gui import flatSlicerWindow
from Cura.gui.util import dropTarget
from Cura.gui.tools import minecraftImport
from Cura.util import validators
from Cura.util import profile
from Cura.util import version
from Cura.util import sliceRun
from Cura.util import meshLoader

class mainWindow(wx.Frame):
	def __init__(self):
		super(mainWindow, self).__init__(None, title='Cura Steam Engine BETA - ' + version.getVersion())

		self.extruderCount = int(profile.getPreference('extruder_amount'))

		wx.EVT_CLOSE(self, self.OnClose)

		self.SetDropTarget(dropTarget.FileDropTarget(self.OnDropFiles, meshLoader.supportedExtensions()))

		self.normalModeOnlyItems = []

		mruFile = os.path.join(profile.getBasePath(), 'mru_filelist.ini')
		self.config = wx.FileConfig(appName="Cura", 
						localFilename=mruFile,
						style=wx.CONFIG_USE_LOCAL_FILE)
						
		self.ID_MRU_MODEL1, self.ID_MRU_MODEL2, self.ID_MRU_MODEL3, self.ID_MRU_MODEL4, self.ID_MRU_MODEL5, self.ID_MRU_MODEL6, self.ID_MRU_MODEL7, self.ID_MRU_MODEL8, self.ID_MRU_MODEL9, self.ID_MRU_MODEL10 = [wx.NewId() for line in xrange(10)]
		self.modelFileHistory = wx.FileHistory(10, self.ID_MRU_MODEL1)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Load(self.config)

		self.ID_MRU_PROFILE1, self.ID_MRU_PROFILE2, self.ID_MRU_PROFILE3, self.ID_MRU_PROFILE4, self.ID_MRU_PROFILE5, self.ID_MRU_PROFILE6, self.ID_MRU_PROFILE7, self.ID_MRU_PROFILE8, self.ID_MRU_PROFILE9, self.ID_MRU_PROFILE10 = [wx.NewId() for line in xrange(10)]
		self.profileFileHistory = wx.FileHistory(10, self.ID_MRU_PROFILE1)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Load(self.config)

		self.menubar = wx.MenuBar()
		self.fileMenu = wx.Menu()
		i = self.fileMenu.Append(-1, 'Load model file...\tCTRL+L')
		self.Bind(wx.EVT_MENU, lambda e: self._showModelLoadDialog(1), i)
		i = self.fileMenu.Append(-1, 'Prepare print...\tCTRL+R')
		self.Bind(wx.EVT_MENU, self.OnSlice, i)
		i = self.fileMenu.Append(-1, 'Print...\tCTRL+P')
		self.Bind(wx.EVT_MENU, self.OnPrint, i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, 'Open Profile...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnLoadProfile, i)
		i = self.fileMenu.Append(-1, 'Save Profile...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnSaveProfile, i)
		i = self.fileMenu.Append(-1, 'Load Profile from GCode...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnLoadProfileFromGcode, i)
		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, 'Reset Profile to default')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnResetProfile, i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, 'Preferences...\tCTRL+,')
		self.Bind(wx.EVT_MENU, self.OnPreferences, i)
		self.fileMenu.AppendSeparator()

		# Model MRU list
		modelHistoryMenu = wx.Menu()
		self.fileMenu.AppendMenu(wx.NewId(), "&Recent Model Files", modelHistoryMenu)
		self.modelFileHistory.UseMenu(modelHistoryMenu)
		self.modelFileHistory.AddFilesToMenu()
		self.Bind(wx.EVT_MENU_RANGE, self.OnModelMRU, id=self.ID_MRU_MODEL1, id2=self.ID_MRU_MODEL10)

		# Profle MRU list
		profileHistoryMenu = wx.Menu()
		self.fileMenu.AppendMenu(wx.NewId(), "&Recent Profile Files", profileHistoryMenu)
		self.profileFileHistory.UseMenu(profileHistoryMenu)
		self.profileFileHistory.AddFilesToMenu()
		self.Bind(wx.EVT_MENU_RANGE, self.OnProfileMRU, id=self.ID_MRU_PROFILE1, id2=self.ID_MRU_PROFILE10)
		
		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(wx.ID_EXIT, 'Quit')
		self.Bind(wx.EVT_MENU, self.OnQuit, i)
		self.menubar.Append(self.fileMenu, '&File')

		toolsMenu = wx.Menu()
		i = toolsMenu.Append(-1, 'Switch to quickprint...')
		self.switchToQuickprintMenuItem = i
		self.Bind(wx.EVT_MENU, self.OnSimpleSwitch, i)
		i = toolsMenu.Append(-1, 'Switch to full settings...')
		self.switchToNormalMenuItem = i
		self.Bind(wx.EVT_MENU, self.OnNormalSwitch, i)
		toolsMenu.AppendSeparator()
		i = toolsMenu.Append(-1, 'Project planner...')
		self.Bind(wx.EVT_MENU, self.OnProjectPlanner, i)
		self.normalModeOnlyItems.append(i)
		i = toolsMenu.Append(-1, 'Batch run...')
		self.Bind(wx.EVT_MENU, self.OnBatchRun, i)
		self.normalModeOnlyItems.append(i)
		#		i = toolsMenu.Append(-1, 'Open SVG (2D) slicer...')
		#		self.Bind(wx.EVT_MENU, self.OnSVGSlicerOpen, i)
		if minecraftImport.hasMinecraft():
			i = toolsMenu.Append(-1, 'Minecraft import...')
			self.Bind(wx.EVT_MENU, self.OnMinecraftImport, i)
		self.menubar.Append(toolsMenu, 'Tools')

		expertMenu = wx.Menu()
		i = expertMenu.Append(-1, 'Open expert settings...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnExpertOpen, i)
		expertMenu.AppendSeparator()
		if firmwareInstall.getDefaultFirmware() is not None:
			i = expertMenu.Append(-1, 'Install default Marlin firmware')
			self.Bind(wx.EVT_MENU, self.OnDefaultMarlinFirmware, i)
		i = expertMenu.Append(-1, 'Install custom firmware')
		self.Bind(wx.EVT_MENU, self.OnCustomFirmware, i)
		expertMenu.AppendSeparator()
		i = expertMenu.Append(-1, 'Run first run wizard...')
		self.Bind(wx.EVT_MENU, self.OnFirstRunWizard, i)
		i = expertMenu.Append(-1, 'Run bed leveling wizard...')
		self.Bind(wx.EVT_MENU, self.OnBedLevelWizard, i)
		self.menubar.Append(expertMenu, 'Expert')

		helpMenu = wx.Menu()
		i = helpMenu.Append(-1, 'Online documentation...')
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('http://daid.github.com/Cura'), i)
		i = helpMenu.Append(-1, 'Report a problem...')
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('https://github.com/daid/Cura/issues'), i)
		i = helpMenu.Append(-1, 'Check for update...')
		self.Bind(wx.EVT_MENU, self.OnCheckForUpdate, i)
		self.menubar.Append(helpMenu, 'Help')
		self.SetMenuBar(self.menubar)

		if profile.getPreference('lastFile') != '':
			self.filelist = profile.getPreference('lastFile').split(';')
			self.SetTitle('Cura - %s - %s' % (version.getVersion(), self.filelist[-1]))
		else:
			self.filelist = []
		self.progressPanelList = []

		self.splitter = wx.SplitterWindow(self, style = wx.SP_3D | wx.SP_LIVE_UPDATE)
		self.leftPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		self.rightPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		self.splitter.Bind(wx.EVT_SPLITTER_DCLICK, lambda evt: evt.Veto())

		##Gui components##
		self.simpleSettingsPanel = simpleMode.simpleModePanel(self.leftPane)
		self.normalSettingsPanel = normalSettingsPanel(self.leftPane)

		self.leftSizer = wx.BoxSizer(wx.VERTICAL)
		self.leftSizer.Add(self.simpleSettingsPanel)
		self.leftSizer.Add(self.normalSettingsPanel, 1, wx.EXPAND)
		self.leftPane.SetSizer(self.leftSizer)
		
		#Preview window
		self.preview3d = preview3d.previewPanel(self.rightPane)

		#Also bind double clicking the 3D preview to load an STL file.
		#self.preview3d.glCanvas.Bind(wx.EVT_LEFT_DCLICK, lambda e: self._showModelLoadDialog(1), self.preview3d.glCanvas)

		#Main sizer, to position the preview window, buttons and tab control
		sizer = wx.BoxSizer()
		self.rightPane.SetSizer(sizer)
		sizer.Add(self.preview3d, 1, flag=wx.EXPAND)

		# Main window sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sizer)
		sizer.Add(self.splitter, 1, wx.EXPAND)
		sizer.Layout()
		self.sizer = sizer

		if len(self.filelist) > 0:
			self.preview3d.loadModelFiles(self.filelist)

			# Update the Model MRU
			for idx in xrange(0, len(self.filelist)):
				self.addToModelMRU(self.filelist[idx])

		self.updateProfileToControls()

		self.SetBackgroundColour(self.normalSettingsPanel.GetBackgroundColour())

		self.simpleSettingsPanel.Show(False)
		self.normalSettingsPanel.Show(False)

		# Set default window size & position
		self.SetSize((wx.Display().GetClientArea().GetWidth()/2,wx.Display().GetClientArea().GetHeight()/2))
		self.Centre()

		# Restore the window position, size & state from the preferences file
		self.normalSashPos = 320
		try:
			if profile.getPreference('window_maximized') == 'True':
				self.Maximize(True)
			else:
				posx = int(profile.getPreference('window_pos_x'))
				posy = int(profile.getPreference('window_pos_y'))
				width = int(profile.getPreference('window_width'))
				height = int(profile.getPreference('window_height'))
			if posx > 0 or posy > 0:
				self.SetPosition((posx,posy))
			if width > 0 and height > 0:
				self.SetSize((width,height))
				
			self.normalSashPos = int(profile.getPreference('window_normal_sash'))
		except:
			self.Maximize(True)

		self.splitter.SplitVertically(self.leftPane, self.rightPane, self.normalSashPos)

		self.updateSliceMode()

		self.Show(True)

	def updateSliceMode(self):
		isSimple = profile.getPreference('startMode') == 'Simple'

		self.normalSettingsPanel.Show(not isSimple)
		self.simpleSettingsPanel.Show(isSimple)
		self.leftPane.Layout()

		for i in self.normalModeOnlyItems:
			i.Enable(not isSimple)
		self.switchToQuickprintMenuItem.Enable(not isSimple)
		self.switchToNormalMenuItem.Enable(isSimple)

		# Set splitter sash position & size
		if isSimple:
			# Save normal mode sash
			self.normalSashPos = self.splitter.GetSashPosition()
			
			# Change location of sash to width of quick mode pane 
			(width, height) = self.simpleSettingsPanel.GetSizer().GetSize() 
			self.splitter.SetSashPosition(width, True)
			
			# Disable sash
			self.splitter.SetSashSize(0)
		else:
			self.splitter.SetSashPosition(self.normalSashPos, True)

			# Enabled sash
			self.splitter.SetSashSize(4)
								
	def OnPreferences(self, e):
		prefDialog = preferencesDialog.preferencesDialog(self)
		prefDialog.Centre()
		prefDialog.Show(True)

	def _showOpenDialog(self, title, wildcard = meshLoader.wildcardFilter()):
		dlg=wx.FileDialog(self, title, os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard(wildcard)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			dlg.Destroy()
			if not(os.path.exists(filename)):
				return False
			profile.putPreference('lastFile', filename)
			return filename
		dlg.Destroy()
		return False

	def _showModelLoadDialog(self, amount):
		filelist = []
		for i in xrange(0, amount):
			filelist.append(self._showOpenDialog("Open file to print"))
			if filelist[-1] == False:
				return
		self._loadModels(filelist)

	def _loadModels(self, filelist):
		self.filelist = filelist
		self.SetTitle('Cura - %s - %s' % (version.getVersion(), filelist[-1]))
		profile.putPreference('lastFile', ';'.join(self.filelist))
		self.preview3d.loadModelFiles(self.filelist, True)
		self.preview3d.setViewMode("Normal")
		
		# Update the Model MRU
		for idx in xrange(0, len(self.filelist)):
			self.addToModelMRU(self.filelist[idx])

	def OnDropFiles(self, files):
		profile.putProfileSetting('model_matrix', '1,0,0,0,1,0,0,0,1')
		profile.setPluginConfig([])
		self.updateProfileToControls()
		self._loadModels(files)

	def OnLoadModel(self, e):
		self._showModelLoadDialog(1)

	def OnLoadModel2(self, e):
		self._showModelLoadDialog(2)

	def OnLoadModel3(self, e):
		self._showModelLoadDialog(3)

	def OnLoadModel4(self, e):
		self._showModelLoadDialog(4)

	def OnSlice(self, e):
		if len(self.filelist) < 1:
			wx.MessageBox('You need to load a file before you can prepare it.', 'Print error', wx.OK | wx.ICON_INFORMATION)
			return
		isSimple = profile.getPreference('startMode') == 'Simple'
		if isSimple:
			#save the current profile so we can put it back latter
			oldProfile = profile.getProfileString()
			self.simpleSettingsPanel.setupSlice()
		#Create a progress panel and add it to the window. The progress panel will start the Skein operation.
		spp = sliceProgressPanel.sliceProgressPanel(self, self, self.filelist)
		self.sizer.Add(spp, 0, flag=wx.EXPAND)
		self.sizer.Layout()
		newSize = self.GetSize()
		newSize.IncBy(0, spp.GetSize().GetHeight())
		if newSize.GetWidth() < wx.GetDisplaySize()[0]:
			self.SetSize(newSize)
		self.progressPanelList.append(spp)
		if isSimple:
			profile.loadProfileFromString(oldProfile)

	def OnPrint(self, e):
		if len(self.filelist) < 1:
			wx.MessageBox('You need to load a file and prepare it before you can print.', 'Print error', wx.OK | wx.ICON_INFORMATION)
			return
		if not os.path.exists(sliceRun.getExportFilename(self.filelist[0])):
			wx.MessageBox('You need to prepare a print before you can run the actual print.', 'Print error', wx.OK | wx.ICON_INFORMATION)
			return
		printWindow.printFile(sliceRun.getExportFilename(self.filelist[0]))

	def OnModelMRU(self, e):
		fileNum = e.GetId() - self.ID_MRU_MODEL1
		path = self.modelFileHistory.GetHistoryFile(fileNum)
		# Update Model MRU
		self.modelFileHistory.AddFileToHistory(path)  # move up the list
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Save(self.config)
		self.config.Flush()
		# Load Model
		filelist = [ path ]
		self._loadModels(filelist)

	def addToModelMRU(self, file):
		self.modelFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Save(self.config)
		self.config.Flush()
	
	def OnProfileMRU(self, e):
		fileNum = e.GetId() - self.ID_MRU_PROFILE1
		path = self.profileFileHistory.GetHistoryFile(fileNum)
		# Update Profile MRU
		self.profileFileHistory.AddFileToHistory(path)  # move up the list
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()
		# Load Profile	
		profile.loadProfile(path)
		self.updateProfileToControls()

	def addToProfileMRU(self, file):
		self.profileFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()			

	def removeSliceProgress(self, spp):
		self.progressPanelList.remove(spp)
		newSize = self.GetSize()
		newSize.IncBy(0, -spp.GetSize().GetHeight())
		if newSize.GetWidth() < wx.GetDisplaySize()[0]:
			self.SetSize(newSize)
		spp.Show(False)
		self.sizer.Detach(spp)
		self.sizer.Layout()

	def updateProfileToControls(self):
		self.preview3d.updateProfileToControls()
		self.normalSettingsPanel.updateProfileToControls()
		self.simpleSettingsPanel.updateProfileToControls()

	def OnLoadProfile(self, e):
		dlg=wx.FileDialog(self, "Select profile file to load", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			profile.loadProfile(profileFile)
			self.updateProfileToControls()

			# Update the Profile MRU
			self.addToProfileMRU(profileFile)
		dlg.Destroy()

	def OnLoadProfileFromGcode(self, e):
		dlg=wx.FileDialog(self, "Select gcode file to load profile from", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("gcode files (*.gcode)|*.gcode;*.g")
		if dlg.ShowModal() == wx.ID_OK:
			gcodeFile = dlg.GetPath()
			f = open(gcodeFile, 'r')
			hasProfile = False
			for line in f:
				if line.startswith(';CURA_PROFILE_STRING:'):
					profile.loadProfileFromString(line[line.find(':')+1:].strip())
					hasProfile = True
			if hasProfile:
				self.updateProfileToControls()
			else:
				wx.MessageBox('No profile found in GCode file.\nThis feature only works with GCode files made by Cura 12.07 or newer.', 'Profile load error', wx.OK | wx.ICON_INFORMATION)
		dlg.Destroy()

	def OnSaveProfile(self, e):
		dlg=wx.FileDialog(self, "Select profile file to save", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			profile.saveProfile(profileFile)
		dlg.Destroy()

	def OnResetProfile(self, e):
		dlg = wx.MessageDialog(self, 'This will reset all profile settings to defaults.\nUnless you have saved your current profile, all settings will be lost!\nDo you really want to reset?', 'Profile reset', wx.YES_NO | wx.ICON_QUESTION)
		result = dlg.ShowModal() == wx.ID_YES
		dlg.Destroy()
		if result:
			profile.resetProfile()
			self.updateProfileToControls()

	def OnBatchRun(self, e):
		br = batchRun.batchRunWindow(self)
		br.Centre()
		br.Show(True)

	def OnSimpleSwitch(self, e):
		profile.putPreference('startMode', 'Simple')
		self.updateSliceMode()

	def OnNormalSwitch(self, e):
		profile.putPreference('startMode', 'Normal')
		self.updateSliceMode()

	def OnDefaultMarlinFirmware(self, e):
		firmwareInstall.InstallFirmware()

	def OnCustomFirmware(self, e):
		if profile.getPreference('machine_type') == 'ultimaker':
			wx.MessageBox('Warning: Installing a custom firmware does not guarantee that you machine will function correctly, and could damage your machine.', 'Firmware update', wx.OK | wx.ICON_EXCLAMATION)
		dlg=wx.FileDialog(self, "Open firmware to upload", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("HEX file (*.hex)|*.hex;*.HEX")
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			if not(os.path.exists(filename)):
				return
			#For some reason my Ubuntu 10.10 crashes here.
			firmwareInstall.InstallFirmware(filename)

	def OnFirstRunWizard(self, e):
		configWizard.configWizard()
		self.updateProfileToControls()

	def OnBedLevelWizard(self, e):
		configWizard.bedLevelWizard()

	def OnExpertOpen(self, e):
		ecw = expertConfig.expertConfigWindow()
		ecw.Centre()
		ecw.Show(True)

	def OnProjectPlanner(self, e):
		pp = projectPlanner.projectPlanner()
		pp.Centre()
		pp.Show(True)

	def OnMinecraftImport(self, e):
		mi = minecraftImport.minecraftImportWindow(self)
		mi.Centre()
		mi.Show(True)

	def OnSVGSlicerOpen(self, e):
		svgSlicer = flatSlicerWindow.flatSlicerWindow()
		svgSlicer.Centre()
		svgSlicer.Show(True)

	def OnCheckForUpdate(self, e):
		newVersion = version.checkForNewerVersion()
		if newVersion is not None:
			if wx.MessageBox('A new version of Cura is available, would you like to download?', 'New version available', wx.YES_NO | wx.ICON_INFORMATION) == wx.YES:
				webbrowser.open(newVersion)
		else:
			wx.MessageBox('You are running the latest version of Cura!', 'Awesome!', wx.ICON_INFORMATION)

	def OnClose(self, e):
		profile.saveProfile(profile.getDefaultProfilePath())

		# Save the window position, size & state from the preferences file
		profile.putPreference('window_maximized', self.IsMaximized())
		if not self.IsMaximized() and not self.IsIconized():
			(posx, posy) = self.GetPosition()
			profile.putPreference('window_pos_x', posx)
			profile.putPreference('window_pos_y', posy)
			(width, height) = self.GetSize()
			profile.putPreference('window_width', width)
			profile.putPreference('window_height', height)			
			
			# Save normal sash position.  If in normal mode (!simple mode), get last position of sash before saving it...
			isSimple = profile.getPreference('startMode') == 'Simple'
			if not isSimple:
				self.normalSashPos = self.splitter.GetSashPosition()
			profile.putPreference('window_normal_sash', self.normalSashPos)

		#HACK: Set the paint function of the glCanvas to nothing so it won't keep refreshing. Which keeps wxWidgets from quiting.
		self.preview3d.glCanvas.OnPaint = lambda e : e
		self.Destroy()

	def OnQuit(self, e):
		self.Close()

class normalSettingsPanel(configBase.configPanelBase):
	"Main user interface window"
	def _addSettingsToPanels(self, category, left, right):
		count = len(profile.getSubCategoriesFor(category)) + len(profile.getSettingsForCategory(category))

		p = left
		n = 0
		for title in profile.getSubCategoriesFor(category):
			n += 1 + len(profile.getSettingsForCategory(category, title))
			if n > count / 2:
				p = right
			configBase.TitleRow(p, title)
			for s in profile.getSettingsForCategory(category, title):
				if s.checkConditions():
					configBase.SettingRow(p, s.getName())

	def __init__(self, parent):
		super(normalSettingsPanel, self).__init__(parent)

		#Main tabs
		self.nb = wx.Notebook(self)
		self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		self.GetSizer().Add(self.nb, 1, wx.EXPAND)

		(left, right, self.printPanel) = self.CreateDynamicConfigTab(self.nb, 'Basic')
		self._addSettingsToPanels('basic', left, right)
		self.SizeLabelWidths(left, right)
		
		(left, right, self.advancedPanel) = self.CreateDynamicConfigTab(self.nb, 'Advanced')
		self._addSettingsToPanels('advanced', left, right)
		self.SizeLabelWidths(left, right)

		#Plugin page
		self.pluginPanel = pluginPanel.pluginPanel(self.nb)
		if len(self.pluginPanel.pluginList) > 0:
			self.nb.AddPage(self.pluginPanel, "Plugins")
		else:
			self.pluginPanel.Show(False)

		#Alteration page
		self.alterationPanel = alterationPanel.alterationPanel(self.nb)
		self.nb.AddPage(self.alterationPanel, "Start/End-GCode")

		self.Bind(wx.EVT_SIZE, self.OnSize)

	def SizeLabelWidths(self, left, right):
		leftWidth = self.getLabelColumnWidth(left)
		rightWidth = self.getLabelColumnWidth(right)
		maxWidth = max(leftWidth, rightWidth)
		self.setLabelColumnWidth(left, maxWidth)
		self.setLabelColumnWidth(right, maxWidth)

	def OnSize(self, e):
		# Make the size of the Notebook control the same size as this control
		self.nb.SetSize(self.GetSize())
		
		# Propegate the OnSize() event (just in case)
		e.Skip()
		
		# Perform out resize magic
		self.UpdateSize(self.printPanel)
		self.UpdateSize(self.advancedPanel)
	
	def UpdateSize(self, configPanel):
		sizer = configPanel.GetSizer()
		
		# Pseudocde
		# if horizontal:
		#     if width(col1) < best_width(col1) || width(col2) < best_width(col2):
		#         switch to vertical
		# else:
		#     if width(col1) > (best_width(col1) + best_width(col1)):
		#         switch to horizontal
		#
				
		col1 = configPanel.leftPanel
		colSize1 = col1.GetSize()
		colBestSize1 = col1.GetBestSize()
		col2 = configPanel.rightPanel
		colSize2 = col2.GetSize()
		colBestSize2 = col2.GetBestSize()

		orientation = sizer.GetOrientation()
		
		if orientation == wx.HORIZONTAL:
			if (colSize1[0] <= colBestSize1[0]) or (colSize2[0] <= colBestSize2[0]):
				configPanel.Freeze()
				sizer = wx.BoxSizer(wx.VERTICAL)
				sizer.Add(configPanel.leftPanel, flag=wx.EXPAND)
				sizer.Add(configPanel.rightPanel, flag=wx.EXPAND)
				configPanel.SetSizer(sizer)
				#sizer.Layout()
				configPanel.Layout()
				self.Layout()
				configPanel.Thaw()
		else:
			if colSize1[0] > (colBestSize1[0] + colBestSize2[0]):
				configPanel.Freeze()
				sizer = wx.BoxSizer(wx.HORIZONTAL)
				sizer.Add(configPanel.leftPanel, proportion=1, border=35, flag=wx.EXPAND)
				sizer.Add(configPanel.rightPanel, proportion=1, flag=wx.EXPAND)
				configPanel.SetSizer(sizer)
				#sizer.Layout()
				configPanel.Layout()
				self.Layout()
				configPanel.Thaw()
				
	def updateProfileToControls(self):
		super(normalSettingsPanel, self).updateProfileToControls()
		self.alterationPanel.updateProfileToControls()
		self.pluginPanel.updateProfileToControls()
