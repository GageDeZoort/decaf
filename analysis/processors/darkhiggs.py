
#!/usr/bin/env python
import lz4.frame as lz4f
import cloudpickle
import json
import pprint
import numpy as np
import awkward
np.seterr(divide='ignore', invalid='ignore', over='ignore')
from coffea.arrays import Initialize
from coffea import hist, processor
from coffea.util import load, save
from optparse import OptionParser
from uproot_methods import TVector2Array, TLorentzVectorArray

class AnalysisProcessor(processor.ProcessorABC):

    lumis = { #Values from https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmVAnalysisSummaryTable                                                      
        '2016': 35.92,
        '2017': 41.53,
        '2018': 59.97
    }

    met_filter_flags = {
     
        '2016': ['goodVertices',
                 'globalSuperTightHalo2016Filter',
                 'HBHENoiseFilter',
                 'HBHENoiseIsoFilter',
                 'EcalDeadCellTriggerPrimitiveFilter'
             ],

        '2017': ['goodVertices',
                 'globalSuperTightHalo2016Filter',
                 'HBHENoiseFilter',
                 'HBHENoiseIsoFilter',
                 'EcalDeadCellTriggerPrimitiveFilter',
                 'BadPFMuonFilter',
             ],

        '2018': ['goodVertices',
                 'globalSuperTightHalo2016Filter',
                 'HBHENoiseFilter',
                 'HBHENoiseIsoFilter',
                 'EcalDeadCellTriggerPrimitiveFilter',
                 'BadPFMuonFilter',
             ]
    }

    

    def __init__(self, year, xsec, corrections, ids, common):

        self._columns = """                                                                                                                    
        MET_pt
        MET_phi
        CaloMET_pt
        CaloMET_phi
        Electron_pt
        Electron_eta
        Electron_phi
        Electron_mass
        Muon_pt
        Muon_eta
        Muon_phi
        Muon_mass
        Tau_pt
        Tau_eta
        Tau_phi
        Tau_mass
        Photon_pt
        Photon_eta
        Photon_phi
        Photon_mass
        AK15Puppi_pt
        AK15Puppi_eta
        AK15Puppi_phi
        AK15Puppi_mass
        Jet_pt
        Jet_eta
        Jet_phi
        Jet_mass
        Jet_btagDeepB
        Jet_btagDeepFlavB
        GenPart_pt
        GenPart_eta
        GenPart_phi
        GenPart_mass
        GenPart_pdgId
        GenPart_status
        GenPart_statusFlags
        GenPart_genPartIdxMother
        PV_npvs
        Electron_cutBased
        Electron_dxy
        Electron_dz
        Muon_pfRelIso04_all
        Muon_tightId
        Muon_mediumId
        Muon_dxy
        Muon_dz
        Tau_idMVAoldDM2017v2
        Tau_idDecayMode
        Photon_cutBased
        Photon_electronVeto
        Photon_cutBasedBitmap
        AK15Puppi_jetId
        Jet_jetId
        Jet_neHEF
        Jet_neEmEF
        Jet_chHEF
        Jet_chEmEF
        AK15Puppi_probTbcq
        AK15Puppi_probTbqq
        AK15Puppi_probTbc
        AK15Puppi_probTbq
        AK15Puppi_probWcq
        AK15Puppi_probWqq
        AK15Puppi_probZbb
        AK15Puppi_probZcc
        AK15Puppi_probZqq
        AK15Puppi_probHbb
        AK15Puppi_probHcc
        AK15Puppi_probHqqqq
        AK15Puppi_probQCDbb
        AK15Puppi_probQCDcc
        AK15Puppi_probQCDb
        AK15Puppi_probQCDc
        AK15Puppi_probQCDothers
        AK15Puppi_msoftdrop
        genWeight
        """.split()
        
        self._year = year

        self._lumi = 1000.*float(AnalysisProcessor.lumis[year])

        self._xsec = xsec

        self._samples = {
            'sr':('ZJets','WJets','DY','TT','ST','WW','WZ','ZZ','QCD','HToBB','MET','Mhs_50','Mhs_70','Mhs_90','MonoJet','MonoW','MonoZ'),
            'wmcr':('WJets','DY','TT','ST','WW','WZ','ZZ','QCD','HToBB','MET'),
            'tmcr':('WJets','DY','TT','ST','WW','WZ','ZZ','QCD','HToBB','MET'),
            'wecr':('WJets','DY','TT','ST','WW','WZ','ZZ','QCD','HToBB','SingleElectron','EGamma'),
            'tecr':('WJets','DY','TT','ST','WW','WZ','ZZ','QCD','HToBB','SingleElectron','EGamma'),
            'zmcr':('WJets','DY','TT','ST','WW','WZ','ZZ','HToBB','MET'),
            'zecr':('WJets','DY','TT','ST','WW','WZ','ZZ','HToBB','SingleElectron','EGamma'),
            'gcr':('GJets','QCD','SinglePhoton','EGamma')
        }

        self._met_triggers = {
            '2016': [
                'PFMETNoMu120_PFMHTNoMu120_IDTight'
            ],
            '2017': [
                'PFMETNoMu120_PFMHTNoMu120_IDTight_PFHT60',
                'PFMETNoMu120_PFMHTNoMu120_IDTight',
            ],
            '2018': [
                'PFMETNoMu120_PFMHTNoMu120_IDTight_PFHT60',
                'PFMETNoMu120_PFMHTNoMu120_IDTight',
            ]
        }

        self._singlephoton_triggers = {
            '2016': [
                'Photon175',
                'Photon165_HE10'
            ],
            '2017': [
                'Photon200'
            ],
            '2018': [
                'Photon200'
            ]
        }

        self._singleelectron_triggers = {
            '2016': [
                'Ele27_WPTight_Gsf',
                'Ele115_CaloIdVT_GsfTrkIdT',
                'Photon175'
            ],
            '2017': [
                'Ele35_WPTight_Gsf',
                'Ele115_CaloIdVT_GsfTrkIdT',
                'Photon200'
            ],
            '2018': [
                'Ele32_WPTight_Gsf',
                'Ele115_CaloIdVT_GsfTrkIdT',
                'Photon200'
            ]
        }


        self._corrections = corrections
        self._ids = ids
        self._common = common

        self._accumulator = processor.dict_accumulator({
            'sumw': hist.Hist('sumw', hist.Cat('dataset', 'Dataset'), hist.Bin('sumw', 'Weight value', [0.])),
            'CaloMinusPfOverRecoil': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('CaloMinusPfOverRecoil','Calo - Pf / Recoil',35,0,1)),
            'recoil': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('recoil','Hadronic Recoil',[250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0, 470.0, 510.0, 550.0, 590.0, 640.0, 690.0, 740.0, 790.0, 840.0, 900.0, 960.0, 1020.0, 1090.0, 1160.0, 1250.0])),
            'mindphi': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('mindphi','Min dPhi(MET,AK4s)',30,0,3.5)),
            'j1pt': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('j1pt','AK4 Leading Jet Pt',[30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0, 470.0, 510.0, 550.0, 590.0, 640.0, 690.0, 740.0, 790.0, 840.0, 900.0, 960.0, 1020.0, 1090.0, 1160.0, 1250.0])),
            'j1eta': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('j1eta','AK4 Leading Jet Eta',35,-3.5,3.5)),
            'j1phi': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('j1phi','AK4 Leading Jet Phi',35,-3.5,3.5)),
            'fj1pt': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('fj1pt','AK15 Leading Jet Pt',[200.0, 250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0, 470.0, 510.0, 550.0, 590.0, 640.0, 690.0, 740.0, 790.0, 840.0, 900.0, 960.0, 1020.0, 1090.0, 1160.0, 1250.0])),
            'fj1eta': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('fj1eta','AK15 Leading Jet Eta',35,-3.5,3.5)),
            'fj1phi': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('fj1phi','AK15 Leading Jet Phi',35,-3.5,3.5)),
            'njets': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('njets','AK4 Number of Jets',6,0,5)),
            'ndcsvL': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('ndcsvL','AK4 Number of deepCSV Loose Jets',6,0,5)),
            'ndflvL': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('ndflvL','AK4 Number of deepFlavor Loose Jets',6,0,5)),
            'nfjtot': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('nfjtot','AK15 Number of Jets',4,0,3)),
            'nfjgood': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('nfjgood','AK15 Number of Good Jets',4,0,3)),
            'nfjclean': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('nfjclean','AK15 Number of cleaned Jets',4,0,3)),
            'fjmass': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('fjmass','AK15 Jet Mass',30,0,300)),
            'e1pt': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('e1pt','Leading Electron Pt',[30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0, 470.0, 510.0, 550.0, 590.0, 640.0, 690.0, 740.0, 790.0, 840.0, 900.0, 960.0, 1020.0, 1090.0, 1160.0, 1250.0])),
            'e1eta': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('e1eta','Leading Electron Eta',48,-2.4,2.4)),
            'e1phi': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('e1phi','Leading Electron Phi',64,-3.2,3.2)),
            'dielemass': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('dielemass','Dielectron mass',100,0,500)),
            'mu1pt': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('mu1pt','Leading Muon Pt',[30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0, 470.0, 510.0, 550.0, 590.0, 640.0, 690.0, 740.0, 790.0, 840.0, 900.0, 960.0, 1020.0, 1090.0, 1160.0, 1250.0])),
            'mu1eta': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('mu1eta','Leading Muon Eta',48,-2.4,2.4)),
            'mu1phi': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('mu1phi','Leading Muon Phi',64,-3.2,3.2)),
            'dimumass': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('dimumass','Dimuon mass',100,0,500)),
            'ZHbbvsQCD': hist.Hist('Events', hist.Cat('dataset', 'Dataset'), hist.Cat('region', 'Region'), hist.Bin('ZHbbvsQCD','ZHbbvsQCD',15,0,1)),
        })

    @property
    def accumulator(self):
        return self._accumulator

    @property
    def columns(self):
        return self._columns

    def process(self, events):

        dataset = events.metadata['dataset']

        selected_regions = []
        for region, samples in self._samples.items():
            for sample in samples:
                if sample not in dataset: continue
                selected_regions.append(region)

        isData = 'genWeight' not in events.columns
        selection = processor.PackedSelection()
        weights = {}
        hout = self.accumulator.identity()
            

        ###
        #Getting corrections, ids from .coffea files
        ###

        get_msd_weight          = self._corrections['get_msd_weight']    
        get_ttbar_weight        = self._corrections['get_ttbar_weight']       
        get_nlo_weight          = self._corrections['get_nlo_weight']         
        get_nnlo_weight         = self._corrections['get_nnlo_weight']
        get_adhoc_weight        = self._corrections['get_adhoc_weight']       
        get_pu_weight           = self._corrections['get_pu_weight']          
        get_met_trig_weight     = self._corrections['get_met_trig_weight']    
        get_met_zmm_trig_weight = self._corrections['get_met_zmm_trig_weight']
        get_ele_trig_weight     = self._corrections['get_ele_trig_weight']    
        get_pho_trig_weight     = self._corrections['get_pho_trig_weight']    
        get_ele_loose_id_sf     = self._corrections['get_ele_loose_id_sf']
        get_ele_tight_id_sf     = self._corrections['get_ele_tight_id_sf']
        get_ele_loose_id_eff    = self._corrections['get_ele_loose_id_eff']
        get_ele_tight_id_eff    = self._corrections['get_ele_tight_id_eff']
        get_pho_tight_id_sf     = self._corrections['get_pho_tight_id_sf']
        get_mu_tight_id_sf      = self._corrections['get_mu_tight_id_sf']
        get_mu_loose_id_sf      = self._corrections['get_mu_loose_id_sf']
        get_ele_reco_sf         = self._corrections['get_ele_reco_sf']
        get_mu_tight_iso_sf     = self._corrections['get_mu_tight_iso_sf']
        get_mu_loose_iso_sf     = self._corrections['get_mu_loose_iso_sf']
        get_ecal_bad_calib      = self._corrections['get_ecal_bad_calib']     
        get_deepflav_weight     = self._corrections['get_btag_weight']['deepflav'][self._year]
        
        isLooseElectron = self._ids['isLooseElectron'] 
        isTightElectron = self._ids['isTightElectron'] 
        isLooseMuon     = self._ids['isLooseMuon']     
        isTightMuon     = self._ids['isTightMuon']     
        isLooseTau      = self._ids['isLooseTau']      
        isLoosePhoton   = self._ids['isLoosePhoton']   
        isTightPhoton   = self._ids['isTightPhoton']   
        isGoodJet       = self._ids['isGoodJet']       
        isGoodFatJet    = self._ids['isGoodFatJet']    
        isHEMJet        = self._ids['isHEMJet']        
        
        match = self._common['match']

        ###
        #Initialize global quantities (MET ecc.)
        ###

        met = events.MET
        met['T'] = TVector2Array.from_polar(met.pt, met.phi)
        calomet = events.CaloMET

        ###
        #Initialize physics objects
        ###

        e = events.Electron
        e['isloose'] = isLooseElectron(e.pt,e.eta,e.dxy,e.dz,e.cutBased,self._year)
        e['istight'] = isTightElectron(e.pt,e.eta,e.cutBased,self._year)
        e['T'] = TVector2Array.from_polar(e.pt, e.phi)
        leading_e = e[e.pt.argmax()]
        leading_e = leading_e[leading_e.istight.astype(np.bool)]
        e_loose = e[e.isloose.astype(np.bool)]
        e_tight = e[e.istight.astype(np.bool)]
        e_ntot = e.counts
        e_nloose = e_loose.counts
        e_ntight = e_tight.counts

        mu = events.Muon
        mu['isloose'] = isLooseMuon(mu.pt,mu.eta,mu.pfRelIso04_all,mu.looseId,self._year)
        mu['istight'] = isTightMuon(mu.pt,mu.eta,mu.pfRelIso04_all,mu.tightId,self._year)
        mu['T'] = TVector2Array.from_polar(mu.pt, mu.phi)
        leading_mu = mu[mu.pt.argmax()]
        leading_mu = leading_mu[leading_mu.istight.astype(np.bool)]
        mu_loose=mu[mu.isloose.astype(np.bool)]
        mu_tight=mu[mu.istight.astype(np.bool)]
        mu_ntot = mu.counts
        mu_nloose = mu_loose.counts
        mu_ntight = mu_tight.counts

        tau = events.Tau
        tau['isclean']=~match(tau,mu_loose,0.5)&~match(tau,e_loose,0.5)
        tau['isloose']=isLooseTau(tau.pt,tau.eta,tau.idDecayMode,tau.idMVAoldDM2017v2,self._year)&tau.isclean.astype(np.bool)
        tau_loose=tau[tau.isloose.astype(np.bool)]
        tau_ntot=tau.counts
        tau_nloose=tau_loose.counts

        pho = events.Photon
        pho['isclean']=~match(pho,mu_loose,0.5)&~match(pho,e_loose,0.5)
        _id = 'cutBasedBitmap'
        if self._year=='2016': _id = 'cutBased'
        pho['isloose']=isLoosePhoton(pho.pt,pho.eta,pho[_id],self._year)&pho.isclean.astype(np.bool)
        pho['istight']=isTightPhoton(pho.pt,pho.eta,pho[_id],self._year)&pho.isclean.astype(np.bool)
        pho['T'] = TVector2Array.from_polar(pho.pt, pho.phi)
        leading_pho = pho[pho.pt.argmax()]
        leading_pho = leading_pho[leading_pho.istight.astype(np.bool)]
        pho_loose=pho[pho.isloose.astype(np.bool)]
        pho_tight=pho[pho.istight.astype(np.bool)]
        pho_ntot=pho.counts
        pho_nloose=pho_loose.counts
        pho_ntight=pho_tight.counts

        sj = events.AK15PuppiSubJet

        fj = events.AK15Puppi
        fj['hassj1'] = (fj.subJetIdx1>-1)
        fj['hassj2'] = (fj.subJetIdx2>-1)
        fj['isgood'] = isGoodFatJet(fj.pt, fj.eta, fj.jetId)
        fj['isclean'] =~match(fj,pho_loose,1.5)&~match(fj,mu_loose,1.5)&~match(fj,e_loose,1.5)&fj.isgood.astype(np.bool)
        fj['msd_corr'] = fj.msoftdrop*awkward.JaggedArray.fromoffsets(fj.array.offsets, get_msd_weight(fj.pt.flatten(),fj.eta.flatten()))
        fj['ZHbbvsQCD'] = (fj.probZbb + fj.probHbb) / (fj.probZbb+ fj.probHbb+ fj.probQCDbb+fj.probQCDcc+fj.probQCDb+fj.probQCDc+fj.probQCDothers)
        fj_good = fj[fj.isgood.astype(np.bool)]
        fj_clean=fj[fj.isclean.astype(np.bool)]
        fj_ntot=fj.counts
        fj_ngood=fj_good.counts
        fj_nclean=fj_clean.counts

        #print(sj[fj[fj.hassj1].subJetIdx1],sj[fj[fj.hassj2].subJetIdx2])
        
        j = events.Jet
        j['isgood'] = isGoodJet(j.pt, j.eta, j.jetId, j.neHEF, j.neEmEF, j.chHEF, j.chEmEF)
        j['isHEM'] = isHEMJet(j.pt, j.eta, j.phi)
        j['isclean'] = ~match(j,e_loose,0.4)&~match(j,mu_loose,0.4)&~match(j,pho_loose,0.4)&j.isgood.astype(np.bool)
        j['isiso'] = ~match(j,fj_clean,1.5)&j.isclean.astype(np.bool)
        j['isdcsvL'] = (j.btagDeepB>0.1241)&j.isiso.astype(np.bool)
        j['isdflvL'] = (j.btagDeepFlavB>0.0494)&j.isiso.astype(np.bool)
        j['T'] = TVector2Array.from_polar(j.pt, j.phi)
        leading_j = j[j.pt.argmax()]
        leading_j = leading_j[leading_j.isclean.astype(np.bool)]
        j_good = j[j.isgood.astype(np.bool)]
        j_clean = j[j.isclean.astype(np.bool)]
        j_iso = j[j.isiso.astype(np.bool)]
        j_dcsvL = j[j.isdcsvL]
        j_dflvL = j[j.isdflvL]
        j_HEM = j[j.isHEM.astype(np.bool)]
        j_ntot=j.counts
        j_ngood=j_good.counts
        j_nclean=j_clean.counts
        j_niso=j_iso.counts
        j_ndcsvL=j_dcsvL.counts
        j_ndflvL=j_dflvL.counts
        j_nHEM = j_HEM.counts

        ###
        #Calculating derivatives
        ###

        ele_pairs = e_loose.distincts()
        #diele = leading_e
        #leading_diele = leading_e
        #if ele_pairs.i0.content.size>0:
        diele = ele_pairs.i0+ele_pairs.i1
        diele['T'] = TVector2Array.from_polar(diele.pt, diele.phi)
        leading_diele = diele[diele.pt.argmax()]

        mu_pairs = mu_loose.distincts()
        #dimu = leading_mu
        #leading_dimu = leading_mu
        #if mu_pairs.i0.content.size>0:
        dimu = mu_pairs.i0+mu_pairs.i1
        dimu['T'] = TVector2Array.from_polar(dimu.pt, dimu.phi)
        leading_dimu = dimu[dimu.pt.argmax()]

        ###
        # Calculate recoil
        ###

        um = met.T+leading_mu.T.sum()
        ue = met.T+leading_e.T.sum()
        umm = met.T+leading_dimu.T.sum()
        uee = met.T+leading_diele.T.sum()
        ua = met.T+leading_pho.T.sum()

        u = {}
        u['sr']=met.T
        u['wecr']=ue
        u['tecr']=ue
        u['wmcr']=um
        u['tmcr']=um
        u['zecr']=uee
        u['zmcr']=umm
        u['gcr']=ua

        ###
        #Calculating weights
        ###

        if not isData:
            gen = events.GenPart

            ###
            # Fat-jet top matching at decay level
            ###
            qFromW = gen[
                (abs(gen.pdgId) <= 5) &
                gen.hasFlags(['fromHardProcess', 'isFirstCopy']) &
                (abs(gen.distinctParent.pdgId) == 24)
            ]
            def topmatch(topid, dR=1.5):
                qFromWFromTop = qFromW[qFromW.distinctParent.distinctParent.pdgId == topid]
                bFromTop = gen[
                    (abs(gen.pdgId) == 5) &
                    gen.hasFlags(['fromHardProcess', 'isFirstCopy']) &
                    (gen.distinctParent.pdgId == topid)
                ]
                jetgenWq = fj.cross(qFromWFromTop, nested=True)
                jetgenb = fj.cross(bFromTop, nested=True)
                return (jetgenWq.i0.delta_r(jetgenWq.i1) < dR).all() & (jetgenb.i0.delta_r(jetgenb.i1) < dR).all()
            fj['isTbqq'] = topmatch(6)|topmatch(-6)
            #print('number of fatjets',fj.counts)
            #print(fj.isTbqq)
            #print('number of matched fatjets',fj[fj.isTbqq].counts)

            ###
            # Fat-jet Z->bb matching at decay level
            ###
            bFromZ = gen[
                (abs(gen.pdgId) == 5) &
                gen.hasFlags(['fromHardProcess', 'isFirstCopy']) &
                (abs(gen.distinctParent.pdgId) == 23)
            ]
            jetgenb = fj.cross(bFromZ, nested=True)
            fj['isZbb']  = (jetgenb.i0.delta_r(jetgenb.i1) < 1.5).all()

            gen['isTop'] = (abs(gen.pdgId)==6)&gen.hasFlags(['fromHardProcess', 'isLastCopy'])
            gen['isW'] = (abs(gen.pdgId)==24)&gen.hasFlags(['fromHardProcess', 'isLastCopy'])
            gen['isZ'] = (abs(gen.pdgId)==23)&gen.hasFlags(['fromHardProcess', 'isLastCopy'])
            gen['isA'] = (abs(gen.pdgId)==22)&gen.hasFlags(['fromHardProcess', 'isLastCopy'])

            genTops = gen[gen.isTop]
            genWs = gen[gen.isW]
            genZs = gen[gen.isZ]
            genAs = gen[gen.isA]
            
            wnlo = np.ones(events.size)
            adhocw = np.ones(events.size)
            if('TTJets' in dataset): 
                wnlo = np.sqrt(get_ttbar_weight(genTops[:,0].pt.sum()) * get_ttbar_weight(genTops[:,1].pt.sum()))
            elif('WJets' in dataset): 
                wnlo = get_nlo_weight[self._year]['w'](genWs.pt.max())
                if self._year != '2016': adhocw = get_adhoc_weight['w'](genWs.pt.max())
            elif('DY' in dataset or 'ZJets' in dataset): 
                wnlo = get_nlo_weight[self._year]['z'](genZs.pt.max())
                if self._year != '2016': adhocw = get_adhoc_weight['z'](genZs.pt.max())
            elif('GJets' in dataset): wnlo = get_nlo_weight[self._year]['a'](genAs.pt.max())
            
            nnlo = np.ones(events.size)
            if('WJets' in dataset):
                nnlo = get_nnlo_weight[self._year]['w'](genWs.pt.max())
            elif('DY' in dataset or 'ZJets' in dataset):
                nnlo = get_nnlo_weight[self._year]['z'](genZs.pt.max())
            elif('GJets' in dataset): 
                nnlo = get_nnlo_weight[self._year]['a'](genAs.pt.max())

            ###
            # Calculate PU weight and systematic variations
            ###

            pu = get_pu_weight[self._year]['cen'](events.PV.npvs)
            puUp = get_pu_weight[self._year]['up'](events.PV.npvs)
            puDown = get_pu_weight[self._year]['down'](events.PV.npvs)

            ###
            # Trigger efficiency weight
            ###

            eff1 = get_ele_trig_weight[self._year](ele_pairs[diele.pt.argmax()].i0.eta.sum(),ele_pairs[diele.pt.argmax()].i0.pt.sum())
            eff2 = get_ele_trig_weight[self._year](ele_pairs[diele.pt.argmax()].i1.eta.sum(),ele_pairs[diele.pt.argmax()].i1.pt.sum())

            trig = {}
            trig['sr'] = get_met_trig_weight[self._year](met.pt)
            trig['wmcr'] = get_met_trig_weight[self._year](um.mag)
            trig['tmcr'] = trig['wmcr'] 
            trig['zmcr'] = get_met_zmm_trig_weight[self._year](umm.mag)
            trig['wecr'] = get_ele_trig_weight[self._year](leading_e.eta.sum(), leading_e.pt.sum())
            trig['tecr'] = trig['wecr']
            #if ele_pairs.i0.content.size>0:
            trig['zecr'] = 1 - (1-eff1)*(1-eff2)
            trig['gcr'] = get_pho_trig_weight[self._year](leading_pho.pt.sum())

            mu1eta=abs(mu_pairs[dimu.pt.argmax()].i0.eta.sum())
            if self._year=='2016':mu1eta=mu_pairs[dimu.pt.argmax()].i0.eta.sum()
            mu2eta=abs(mu_pairs[dimu.pt.argmax()].i1.eta.sum())
            if self._year=='2016':mu1eta=mu_pairs[dimu.pt.argmax()].i1.eta.sum()
            mu1lsf=get_mu_loose_id_sf[self._year](mu1eta,mu_pairs[dimu.pt.argmax()].i0.pt.sum())
            mu2lsf=get_mu_loose_id_sf[self._year](mu2eta,mu_pairs[dimu.pt.argmax()].i1.pt.sum())
            mu1tsf=get_mu_tight_id_sf[self._year](mu1eta,mu_pairs[dimu.pt.argmax()].i0.pt.sum())
            mu2tsf=get_mu_tight_id_sf[self._year](mu2eta,mu_pairs[dimu.pt.argmax()].i1.pt.sum())
            mueta = abs(leading_mu.eta.sum())
            if self._year=='2016':mueta=leading_mu.eta.sum()

            e1lsf=get_ele_loose_id_sf[self._year](ele_pairs[diele.pt.argmax()].i0.eta.sum(),ele_pairs[diele.pt.argmax()].i0.pt.sum())
            e1leff= get_ele_loose_id_eff[self._year](ele_pairs[diele.pt.argmax()].i0.eta.sum(),ele_pairs[diele.pt.argmax()].i0.pt.sum())
            e2lsf=get_ele_loose_id_sf[self._year](ele_pairs[diele.pt.argmax()].i1.eta.sum(),ele_pairs[diele.pt.argmax()].i1.pt.sum())
            e2leff= get_ele_loose_id_eff[self._year](ele_pairs[diele.pt.argmax()].i1.eta.sum(),ele_pairs[diele.pt.argmax()].i1.pt.sum())
            e1tsf=get_ele_tight_id_sf[self._year](ele_pairs[diele.pt.argmax()].i0.eta.sum(),ele_pairs[diele.pt.argmax()].i0.pt.sum())
            e1teff= get_ele_tight_id_eff[self._year](ele_pairs[diele.pt.argmax()].i0.eta.sum(),ele_pairs[diele.pt.argmax()].i0.pt.sum())
            e2tsf=get_ele_tight_id_sf[self._year](ele_pairs[diele.pt.argmax()].i1.eta.sum(),ele_pairs[diele.pt.argmax()].i1.pt.sum())
            e2teff= get_ele_tight_id_eff[self._year](ele_pairs[diele.pt.argmax()].i1.eta.sum(),ele_pairs[diele.pt.argmax()].i1.pt.sum())

            ids={}
            ids['sr'] = np.ones(events.size)
            ids['wmcr'] = get_mu_tight_id_sf[self._year](mueta,leading_mu.pt.sum())
            ids['tmcr'] = get_mu_tight_id_sf[self._year](mueta,leading_mu.pt.sum())
            ids['zmcr'] = ((mu1tsf*mu2lsf)+(mu1lsf*mu2tsf))/2.
            ids['wecr'] = get_ele_tight_id_sf[self._year](leading_e.eta.sum(),leading_e.pt.sum())
            ids['tecr'] = get_ele_tight_id_sf[self._year](leading_e.eta.sum(),leading_e.pt.sum())
            ids['zecr'] = ((e1lsf*e1leff*e2tsf*e2teff)+(e2lsf*e2leff*e1tsf*e1teff))/((e1leff*e2teff)+(e1teff*e2leff))
            ids['gcr']  = get_pho_tight_id_sf[self._year](leading_pho.eta.sum(),leading_pho.pt.sum())
            
            reco = {}
            reco['sr'] = np.ones(events.size)
            reco['wmcr'] = np.ones(events.size)
            reco['tmcr'] = np.ones(events.size)
            reco['zmcr'] = np.ones(events.size)
            reco['wecr'] = get_ele_reco_sf[self._year](leading_e.eta.sum(),leading_e.pt.sum())
            reco['tecr'] = get_ele_reco_sf[self._year](leading_e.eta.sum(),leading_e.pt.sum())
            reco['zecr'] = get_ele_reco_sf[self._year](ele_pairs[diele.pt.argmax()].i0.eta.sum(),ele_pairs[diele.pt.argmax()].i0.pt.sum())*get_ele_reco_sf[self._year](ele_pairs[diele.pt.argmax()].i1.eta.sum(),ele_pairs[diele.pt.argmax()].i1.pt.sum())
            reco['gcr'] = np.ones(events.size)

            mu1lisosf = get_mu_loose_iso_sf[self._year](mu1eta,leading_mu.pt.sum())
            mu1tisosf = get_mu_tight_iso_sf[self._year](mu1eta,leading_mu.pt.sum())
            mu2lisosf = get_mu_loose_iso_sf[self._year](mu2eta,leading_mu.pt.sum())
            mu2tisosf = get_mu_tight_iso_sf[self._year](mu2eta,leading_mu.pt.sum())

            isolation = {}
            isolation['sr'] = np.ones(events.size)
            isolation['wmcr'] = get_mu_tight_iso_sf[self._year](mueta,leading_mu.pt.sum())
            isolation['tmcr'] = get_mu_tight_iso_sf[self._year](mueta,leading_mu.pt.sum())
            isolation['zmcr'] = ((mu1tisosf*mu2lisosf)+(mu1lisosf*mu2tisosf))/2.
            isolation['wecr'] = np.ones(events.size)
            isolation['tecr'] = np.ones(events.size)
            isolation['zecr'] = np.ones(events.size)
            isolation['gcr'] = np.ones(events.size)

            btag = {}
            btagUp = {}
            btagDown = {}
            btag['sr'], btagUp['sr'], btagDown['sr'] = get_deepflav_weight['loose'](j_iso.pt,j_iso.eta,j_iso.hadronFlavour,'0')
            btag['wmcr'], btagUp['wmcr'], btagDown['wmcr'] = get_deepflav_weight['loose'](j_iso.pt,j_iso.eta,j_iso.hadronFlavour,'0')
            btag['tmcr'], btagUp['tmcr'], btagDown['tmcr'] = get_deepflav_weight['loose'](j_iso.pt,j_iso.eta,j_iso.hadronFlavour,'-1')
            btag['wecr'], btagUp['wecr'], btagDown['wecr'] = get_deepflav_weight['loose'](j_iso.pt,j_iso.eta,j_iso.hadronFlavour,'0')
            btag['tecr'], btagUp['tecr'], btagDown['tecr'] = get_deepflav_weight['loose'](j_iso.pt,j_iso.eta,j_iso.hadronFlavour,'-1')
            btag['zmcr'], btagUp['zmcr'], btagDown['zmcr'] = get_deepflav_weight['loose'](j_iso.pt,j_iso.eta,j_iso.hadronFlavour,'0')
            btag['zecr'], btagUp['zecr'], btagDown['zecr'] = get_deepflav_weight['loose'](j_iso.pt,j_iso.eta,j_iso.hadronFlavour,'0')
            btag['gcr'], btagUp['gcr'], btagDown['gcr'] = get_deepflav_weight['loose'](j_iso.pt,j_iso.eta,j_iso.hadronFlavour,'0')
            
            for r in selected_regions:
                weights[r] = processor.Weights(len(events))
                weights[r].add('genw',events.genWeight)
                #weights[r].add('nlo',wnlo)
                #weights[r].add('adhoc',adhocw)
                weights[r].add('nnlo',nnlo)
                weights[r].add('pileup',pu,puUp,puDown)
                weights[r].add('trig', trig[r])
                weights[r].add('ids', ids[r])
                weights[r].add('reco', reco[r])
                weights[r].add('isolation', isolation[r])
                weights[r].add('btag',btag[r], btagUp[r], btagDown[r])

        leading_fj = fj[fj.pt.argmax()]
        leading_fj = leading_fj[leading_fj.isclean.astype(np.bool)]
        
        ###
        #Importing the MET filters per year from metfilters.py and constructing the filter boolean
        ###

        met_filters =  np.ones(events.size, dtype=np.bool)
        for flag in AnalysisProcessor.met_filter_flags[self._year]:
            met_filters = met_filters & events.Flag[flag]
        selection.add('met_filters',met_filters)

        triggers = np.zeros(events.size, dtype=np.bool)
        for path in self._met_triggers[self._year]:
            triggers = triggers | events.HLT[path]
        selection.add('met_triggers', triggers)

        triggers = np.zeros(events.size, dtype=np.bool)
        for path in self._singleelectron_triggers[self._year]:
            triggers = triggers | events.HLT[path]
        selection.add('singleelectron_triggers', triggers)

        triggers = np.zeros(events.size, dtype=np.bool)
        for path in self._singlephoton_triggers[self._year]:
            triggers = triggers | events.HLT[path]
        selection.add('singlephoton_triggers', triggers)

        selection.add('iszeroL',
                      (e_nloose==0)&(mu_nloose==0)&(tau_nloose==0)&(pho_nloose==0)
                      &(abs(met.T.delta_phi(j_clean.T)).min()>0.8)
                      &(met.pt>250)
                  )
        selection.add('isoneM', 
                      (e_nloose==0)&(mu_ntight==1)&(tau_nloose==0)&(pho_nloose==0)
                      &(abs(um.delta_phi(j_clean.T)).min()>0.8)
                    &(um.mag>250)
                  )
        selection.add('isoneE', 
                      (e_ntight==1)&(mu_nloose==0)&(tau_nloose==0)&(pho_nloose==0)
                      &(met.pt>50)
                      &(abs(ue.delta_phi(j_clean.T)).min()>0.8)
                      &(ue.mag>250)
                  )
        selection.add('istwoM', 
                      (e_nloose==0)&(mu_ntight>=1)&(mu_nloose==2)&(tau_nloose==0)&(pho_nloose==0)
                      &(leading_dimu.mass.sum()>60)&(leading_dimu.mass.sum()<120)
                      &(abs(umm.delta_phi(j_clean.T)).min()>0.8)
                      &(umm.mag>250)
                  )
        selection.add('istwoE', 
                      (e_ntight>=1)&(e_nloose==2)&(mu_nloose==0)&(tau_nloose==0)&(pho_nloose==0)
                      &(leading_diele.mass.sum()>60)&(leading_diele.mass.sum()<120)
                      &(abs(uee.delta_phi(j_clean.T)).min()>0.8)
                      &(uee.mag>250)
                  )
        selection.add('isoneA', 
                      (e_nloose==0)&(mu_nloose==0)&(tau_nloose==0)&(pho_ntight==1)
                      &(abs(ua.delta_phi(j_clean.T)).min()>0.8)
                      &(ua.mag>250)
                  )
        selection.add('monohs', (leading_fj.ZHbbvsQCD.sum()>0.65))
        selection.add('monojet', ~(leading_fj.ZHbbvsQCD.sum()>0.65))
        selection.add('noextrab', (j_ndflvL==0))
        selection.add('extrab', (j_ndflvL>0))
        selection.add('mass0', (leading_fj.msd_corr.sum()<30))
        selection.add('mass1', (leading_fj.msd_corr.sum()>=30)&(leading_fj.msd_corr.sum()<60))
        selection.add('mass2', (leading_fj.msd_corr.sum()>=60)&(leading_fj.msd_corr.sum()<80))
        selection.add('mass3', (leading_fj.msd_corr.sum()>=80)&(leading_fj.msd_corr.sum()<120))
        selection.add('mass4', (leading_fj.msd_corr.sum()>=120))
        selection.add('noHEMj', (j_nHEM==0))
        selection.add('fatjet', (fj_nclean>0)&(fj_clean.pt.max()>160))

        regions = {}
        regions['sr']={'iszeroL','fatjet','noextrab','noHEMj','met_filters','met_triggers'}
        regions['wmcr']={'isoneM','fatjet','noextrab','noHEMj','met_filters','met_triggers'}
        regions['wecr']={'isoneE','fatjet','noextrab','noHEMj','met_filters','singleelectron_triggers'}
        regions['tmcr']={'isoneM','fatjet','extrab','noHEMj','met_filters','met_triggers'}
        regions['tecr']={'isoneE','fatjet','extrab','noHEMj','met_filters','singleelectron_triggers'}
        regions['zmcr']={'istwoM','fatjet','noextrab','noHEMj','met_filters','met_triggers'}
        regions['zecr']={'istwoE','fatjet','noextrab','noHEMj','met_filters','singleelectron_triggers'}
        regions['gcr']={'isoneA','fatjet','noextrab','noHEMj','met_filters','singlephoton_triggers'}

        temp={}
        for r in selected_regions: 
            temp[r]=regions[r]
        regions=temp
        temp={}
        for r in regions:
            for mass in ['mass0','mass1','mass2','mass3','mass4']:
                temp[r+'_'+mass]={mass}
                temp[r+'_'+mass].update(regions[r])
        regions.update(temp)
        temp={}
        for r in regions:
            for category in ['monojet','monohs']:
                temp[r+'_'+category]={category}
                temp[r+'_'+category].update(regions[r])
        regions.update(temp)

        def fill(dataset, region, weight, cut):
            variables = {}
            variables['j1pt'] = leading_j.pt
            variables['j1eta'] = leading_j.eta
            variables['j1phi'] = leading_j.phi
            variables['fj1pt'] = leading_fj.pt
            variables['fj1eta'] = leading_fj.eta
            variables['fj1phi'] = leading_fj.phi
            variables['e1pt'] = leading_e.pt
            variables['e1phi'] = leading_e.phi
            variables['e1eta'] = leading_e.eta
            variables['dielemass'] = leading_diele.mass
            variables['mu1pt'] = leading_mu.pt
            variables['mu1phi'] = leading_mu.phi
            variables['mu1eta'] = leading_mu.eta
            variables['dimumass'] = leading_dimu.mass
            variables['njets'] = j_nclean
            variables['ndcsvL'] = j_ndcsvL
            variables['ndflvL'] = j_ndflvL
            variables['nfjtot'] = fj_ntot
            variables['nfjgood'] = fj_ngood
            variables['nfjclean'] = fj_nclean
            variables['ZHbbvsQCD'] = leading_fj.ZHbbvsQCD
            flat_variables = {k: v[cut].flatten() for k, v in variables.items()}
            flat_weights = {k: (~np.isnan(v[cut])*weight[cut]).flatten() for k, v in variables.items()}
            if not isData: hout['sumw'].fill(dataset=dataset, sumw=1, weight=events.genWeight.sum())
            for histname, h in hout.items():
                if not isinstance(h, hist.Hist):
                    continue
                elif histname == 'sumw':
                    continue
                elif histname == 'fjmass':
                    h.fill(dataset=dataset, region=region, fjmass=leading_fj.msd_corr.sum(), weight=weight*cut)
                elif histname == 'recoil':
                    h.fill(dataset=dataset, region=region, recoil=u[region.split('_')[0]].mag, weight=weight*cut)
                elif histname == 'CaloMinusPfOverRecoil':
                    h.fill(dataset=dataset, region=region, CaloMinusPfOverRecoil= abs(calomet.pt - met.pt) / u[region.split('_')[0]].mag, weight=weight*cut)
                elif histname == 'mindphi':
                    h.fill(dataset=dataset, region=region, mindphi=abs(u[region.split('_')[0]].delta_phi(j_clean.T)).min(), weight=weight*cut)
                else:
                    flat_variable = {histname: flat_variables[histname]}
                    h.fill(dataset=dataset, region=region, **flat_variable, weight=flat_weights[histname])

        def get_weight(region,systematic=None):
            region=region.split('_')[0]
            if systematic is not None: return weights[region].weight(modifier=systematic)
            return weights[region].weight()
        
        for r in regions:
            cut = selection.all(*regions[r])
            if 'TT' in dataset or 'ST' in dataset:
                wmerged = leading_fj.isTbqq.sum()
                wmerged = get_weight(r)*wmerged
                fill('merged--'+dataset, r, wmerged, cut)
                wunmerged = (~(leading_fj.isTbqq.sum().astype(np.bool))).astype(np.int)
                wunmerged = get_weight(r)*wunmerged
                fill('unmerged--'+dataset, r, wunmerged, cut)
            elif 'WZ' in dataset or 'ZZ' in dataset:
                wbb = leading_fj.isZbb.sum()
                wbb = get_weight(r)*wbb
                fill('bb--'+dataset, r, wbb, cut)
                wother = (~(leading_fj.isZbb.sum().astype(np.bool))).astype(np.int)
                wother = get_weight(r)*wother
                fill(dataset, r, wother, cut)
            elif isData:
                fill(dataset, r, np.ones(events.size), cut)
            else:
                fill(dataset, r, get_weight(r), cut)
        return hout

    def postprocess(self, accumulator):
        scale = {}
        for d in accumulator['sumw'].identifiers('dataset'):
            print('Scaling:',d.name)
            dataset = d.name
            if '--' in dataset: dataset = dataset.split('--')[1]
            if self._xsec[dataset]!= -1: scale[d.name] = self._lumi*self._xsec[dataset]
            else: scale[d.name] = 1

        for histname, h in accumulator.items():
            if histname == 'sumw': continue
            if isinstance(h, hist.Hist):
                h.scale(scale, axis='dataset')

        return accumulator

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-y', '--year', help='year', dest='year')
    (options, args) = parser.parse_args()


    with open('metadata/'+options.year+'.json') as fin:
        samplefiles = json.load(fin)
        xsec = {k: v['xs'] for k,v in samplefiles.items()}

    corrections = load('data/corrections.coffea')
    ids         = load('data/ids.coffea')
    common      = load('data/common.coffea')

    processor_instance=AnalysisProcessor(year=options.year,
                                         xsec=xsec,
                                         corrections=corrections,
                                         ids=ids,
                                         common=common)
    
    save(processor_instance, 'data/darkhiggs'+options.year+'.processor')
