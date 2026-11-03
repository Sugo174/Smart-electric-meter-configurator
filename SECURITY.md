# Security policy

## Reporting a vulnerability

Do not publish confidential information or working exploit
details in a public issue.

Contact the maintainer through an available private channel
and provide a sanitized description containing:

- the affected application version;
- the conditions required to reproduce the problem;
- the expected and actual behaviour;
- the potential impact.

If no private contact channel is available, open an issue
requesting one without disclosing vulnerability details.

## Sensitive information

Before sharing screenshots, videos, communication captures,
or diagnostic materials, remove:

- customer and personal information;
- confidential meter identifiers and production data;
- credentials, access keys, and internal network details.

Do not commit confidential register maps or other restricted
manufacturer documentation without permission.

## Device operations

The application can change meter settings, synchronize its clock,
and clear accumulated energy values.

Access to the computer and the connected RS-485 interface
must be limited to authorized users.

Application confirmation dialogs help prevent accidental actions.
They do not replace device access controls or organizational
authorization procedures.

Verify the connected meter before writing settings or clearing energy.

## Distribution

Use the project's GitHub Releases or an approved internal
distribution channel.

Keep packaged application files together and do not combine
files from different versions.

Report suspected modification of a distributed package
through a private channel.