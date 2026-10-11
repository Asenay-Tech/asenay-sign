export type BuildEnvelopeEmailHeadersOptions = {
  userId: number;
  envelopeId: string;
  teamId: number;
};

/**
 * Builds opaque sender-attribution headers stamped onto outgoing user-triggered
 * envelope emails. These appear in AWS SES bounce/complaint notifications (when
 * "include original headers" is enabled) so an abusive send can be traced back
 * to the originating Asenay Sign user via the admin panel.
 *
 * Only opaque IDs are included so recipients cannot see the sender's email
 * address or name in the delivered message source.
 */
export const buildEnvelopeEmailHeaders = ({
  userId,
  envelopeId,
  teamId,
}: BuildEnvelopeEmailHeadersOptions): Record<string, string> => {
  return {
    'X-Asenay Sign-Sender-User-Id': String(userId),
    'X-Asenay Sign-Envelope-Id': envelopeId,
    'X-Asenay Sign-Team-Id': String(teamId),
  };
};
