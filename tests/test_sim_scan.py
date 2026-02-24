from antennalab.analysis.spectrum import ScanSimulator


def test_sim_scan_bins_count():
    sim = ScanSimulator(seed=123)
    scan = sim.simulate_scan(start_hz=100.0, stop_hz=200.0, bin_hz=10.0)
    assert len(scan.bins) == 10
    assert scan.bins[0].freq_hz == 100.0
    assert scan.bins[-1].freq_hz == 190.0
