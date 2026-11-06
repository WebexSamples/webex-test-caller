import { describe, expect, it } from "vitest";
import { readOutboundAudio, verifyAudioDelivery } from "./audio-delivery";

const before = { packetsSent: 10, bytesSent: 100, totalAudioEnergy: 0, totalSamplesDuration: 1 };
const after = { packetsSent: 20, bytesSent: 500, totalAudioEnergy: 0.2, totalSamplesDuration: 3 };

describe("outbound caller speech evidence", () => {
  it("requires transmitted packets, bytes, and non-silent source audio", () => {
    expect(verifyAudioDelivery(before, after)).toEqual({
      packetsSentDelta: 10,
      bytesSentDelta: 400,
      audioEnergyDelta: 0.2,
      audioDurationSeconds: 2,
    });
  });

  it.each(Object.keys(after) as Array<keyof typeof after>)(
    "rejects playback without an increase in %s",
    (field) => {
      expect(() => verifyAudioDelivery(before, { ...after, [field]: before[field] })).toThrow("non-silent outbound RTP");
    },
  );

  it("reads only the media source associated with the outbound audio stream", async () => {
    const stats = new Map([
      ["rtp", { type: "outbound-rtp", kind: "audio", mediaSourceId: "caller", packetsSent: 20, bytesSent: 500 }],
      ["unrelated", { type: "media-source", kind: "audio", totalAudioEnergy: 999, totalSamplesDuration: 999 }],
      ["caller", { type: "media-source", kind: "audio", totalAudioEnergy: 0.2, totalSamplesDuration: 3 }],
    ]);
    expect(await readOutboundAudio({ getStats: async () => stats as unknown as RTCStatsReport })).toEqual(after);
  });

  it("rejects missing sender evidence", async () => {
    await expect(readOutboundAudio({ getStats: async () => new Map() as unknown as RTCStatsReport })).rejects.toThrow("statistics are unavailable");
  });
});
