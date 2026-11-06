export type OutboundAudio = {
  packetsSent: number;
  bytesSent: number;
  totalAudioEnergy: number;
  totalSamplesDuration: number;
};

export async function readOutboundAudio(
  sender: Pick<RTCRtpSender, "getStats">,
): Promise<OutboundAudio> {
  const stats = await sender.getStats();
  const outbound = Array.from(stats.values()).find(
    (entry) => entry.type === "outbound-rtp" && entry.kind === "audio",
  );
  const source = stats.get(outbound?.mediaSourceId);
  if (!outbound || source?.type !== "media-source" || source.kind !== "audio") {
    throw new Error("Outbound audio RTP/source statistics are unavailable");
  }
  return {
    packetsSent: outbound.packetsSent,
    bytesSent: outbound.bytesSent,
    totalAudioEnergy: source.totalAudioEnergy,
    totalSamplesDuration: source.totalSamplesDuration,
  };
}

export function verifyAudioDelivery(before: OutboundAudio, after: OutboundAudio) {
  const deltas = {
    packetsSentDelta: after.packetsSent - before.packetsSent,
    bytesSentDelta: after.bytesSent - before.bytesSent,
    audioEnergyDelta: after.totalAudioEnergy - before.totalAudioEnergy,
    audioDurationSeconds: after.totalSamplesDuration - before.totalSamplesDuration,
  };
  if (!Object.values(deltas).every((value) => Number.isFinite(value) && value > 0)) {
    throw new Error("Caller speech did not produce non-silent outbound RTP audio");
  }
  return deltas;
}
