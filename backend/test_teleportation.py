from teleportation import run_teleportation


result = run_teleportation(shots=20)

print("\n==============================")
print("QUANTUM TELEPORTATION TEST")
print("==============================")

print("Bell Measurement:")
print(result["bell_measurement"])

print("\nPauli Correction:")
print(result["pauli_correction"])

print("\nVerification:")
print(result["verification"])

print("\nSuccess Rate:")
print(result["teleportation_success_rate"])

print("\nLatency:")
print(result["latency_ms"], "ms")

print("==============================")
